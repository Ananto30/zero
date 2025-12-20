import asyncio
import logging
from dataclasses import dataclass
from typing import Any, List, Optional, Type, TypeVar

from zero.encoder import Encoder
from zero.error import ConnectionException, TimeoutException
from zero.utils.type_util import AllowedType

from .frame_io import read_frame, write_frame

T = TypeVar("T")


class AsyncTCPClient:
    def __init__(
        self,
        address: str,
        default_timeout: int,
        encoder: Encoder,
        pool_size: int,
    ):
        self._encoder = encoder
        self._default_timeout = default_timeout

        # Parse address (handle tcp://host:port or host:port)
        addr = address
        if addr.startswith("tcp://"):
            addr = addr[6:]
        host, port_str = addr.rsplit(":", 1)
        self._host = host
        self._port = int(port_str)

        self._pool = AsyncTCPConnPool(self._host, self._port, encoder, pool_size)
        self._pool_started = False
        self._pool_lock = asyncio.Lock()

    async def _ensure_pool_started(self) -> None:
        if self._pool_started:
            return
        async with self._pool_lock:
            # Double-check pattern to avoid race condition
            if not self._pool_started:
                try:
                    await self._pool.start()
                    self._pool_started = True
                except OSError as e:
                    raise ConnectionException(
                        f"Failed to connect to {self._host}:{self._port}: {e}"
                    ) from e

    async def call(
        self,
        rpc_func_name: str,
        msg: AllowedType,
        timeout: Optional[int] = None,
        return_type: Optional[Type[T]] = None,
    ) -> Optional[T]:
        await self._ensure_pool_started()

        conn = await self._pool.acquire()
        conn_broken = False
        try:
            request = {"fn": rpc_func_name, "data": msg}
            _timeout = timeout or self._default_timeout
            # Convert timeout from milliseconds to seconds for asyncio.wait_for
            _timeout_seconds = _timeout / 1000
            try:
                response = await asyncio.wait_for(
                    conn.request(request), timeout=_timeout_seconds
                )
            except asyncio.TimeoutError as e:
                # Timeout: Check if connection is still alive before deciding to close it.
                # A timeout doesn't necessarily mean the connection is broken—the server
                # might just be slow. However, the delayed response will corrupt the buffer
                # if we reuse the connection. So we always mark it as broken after timeout.
                # (In the future, we could implement a graceful drain of the delayed response.)
                conn_broken = True
                raise TimeoutException(f"Call timed out after {_timeout}ms") from e

            # Return the full response dict so check_response() can handle errors
            # For normal responses, extract data; for error responses, return the dict as-is
            if isinstance(response, dict) and "data" in response:
                data = response["data"]
                return (
                    data
                    if return_type is None
                    else self._encoder.decode_type(data, return_type)
                )

            # Response contains error keys like __zerror__*, return as-is for check_response()
            return response

        finally:
            await self._pool.release(conn, broken=conn_broken)

    def close(self) -> None:
        # Note: close() is sync but pool.close() is async
        # We'll schedule it to run if there's an event loop
        try:
            loop = asyncio.get_running_loop()
            # If there's a running loop, we can't await here
            # So we create a task that will close the pool
            asyncio.create_task(self._pool.close())
        except RuntimeError:
            # No running loop, try to get the event loop and run it
            try:
                loop = asyncio.get_event_loop()
                if loop.is_closed():
                    return
                loop.run_until_complete(self._pool.close())
            except Exception:  # pylint: disable=broad-except
                pass


@dataclass
class PooledTCPConn:
    """A single pooled TCP connection with per-connection lock."""

    reader: asyncio.StreamReader
    writer: asyncio.StreamWriter
    encoder: Encoder
    lock: asyncio.Lock  # ensures 1 in-flight req per connection, simple & safe

    async def request(self, obj: Any) -> Any:
        async with self.lock:
            await write_frame(self.writer, obj, self.encoder)
            return await read_frame(self.reader, self.encoder)

    async def close(self) -> None:
        try:
            self.writer.close()
            await self.writer.wait_closed()
        except Exception:  # pylint: disable=broad-except
            pass


class AsyncTCPConnPool:
    """
    Fixed-size pool of TCP connections.
    Each connection is used by at most one coroutine at a time (via per-conn lock).
    Connections are managed via an asyncio.Queue for fair distribution.
    """

    def __init__(self, host: str, port: int, encoder: Encoder, size: int):
        self._host = host
        self._port = port
        self._encoder = encoder
        self._size = size
        self._q: asyncio.Queue[PooledTCPConn] = asyncio.Queue(maxsize=size)
        self._all: List[PooledTCPConn] = []
        self._started = False
        self._replacing: set[int] = set()  # Track connection IDs being replaced

    async def start(self) -> None:
        if self._started:
            return

        for _ in range(self._size):
            reader, writer = await asyncio.open_connection(self._host, self._port)
            conn = PooledTCPConn(
                reader=reader,
                writer=writer,
                encoder=self._encoder,
                lock=asyncio.Lock(),
            )
            self._all.append(conn)
            self._q.put_nowait(conn)

        self._started = True
        logging.debug("TCP connection pool initialized with %d connections", self._size)

    async def acquire(self) -> PooledTCPConn:
        # Get connections, skipping any that are currently being replaced
        while True:
            conn = await self._q.get()
            if id(conn) not in self._replacing:
                return conn
            # This connection is being replaced, put it back and try again
            await self._q.put(conn)

    async def release(self, conn: PooledTCPConn, broken: bool = False) -> None:
        if broken:
            await conn.close()
            self._replacing.add(id(conn))
            # Create a background task to replace the connection asynchronously
            asyncio.create_task(self._replace_connection_async(conn))
        else:
            # Add health check/reconnect logic here if needed
            await self._q.put(conn)

    async def _replace_connection_async(self, old_conn: PooledTCPConn) -> None:
        old_conn_id = id(old_conn)
        retry_count = 0
        max_wait = 30  # seconds

        while True:
            try:
                reader, writer = await asyncio.open_connection(self._host, self._port)
                new_conn = PooledTCPConn(
                    reader=reader,
                    writer=writer,
                    encoder=self._encoder,
                    lock=asyncio.Lock(),
                )
                # Replace in all list and put in queue
                idx = self._all.index(old_conn)
                self._all[idx] = new_conn
                self._replacing.discard(old_conn_id)
                await self._q.put(new_conn)
                logging.info("Replaced broken connection after %d retries", retry_count)
                return
            except Exception as e:  # pylint: disable=broad-except
                retry_count += 1
                # Exponential backoff with max wait
                wait_time = min(2 ** min(retry_count, 5), max_wait)
                logging.warning(
                    "Failed to create replacement connection (retry %d), "
                    "waiting %ds before retry: %s",
                    retry_count,
                    wait_time,
                    e,
                    exc_info=e,
                    stack_info=True,
                )
                await asyncio.sleep(wait_time)

    async def close(self) -> None:
        for c in self._all:
            await c.close()
