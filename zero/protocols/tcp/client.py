import asyncio
import logging
import sys
from dataclasses import dataclass
from typing import Any, List, Optional, Tuple, Type, TypeVar

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
        if sys.platform == "win32":
            raise RuntimeError("AsyncTCPClient is not supported on Windows")

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
        try:
            request = {"fn": rpc_func_name, "data": msg}
            _timeout = timeout or self._default_timeout
            # Convert timeout from milliseconds to seconds for asyncio.wait_for
            _timeout_seconds = _timeout / 1000

            try:
                response_bytes, is_error = await asyncio.wait_for(
                    conn.request(request), timeout=_timeout_seconds
                )

            except asyncio.TimeoutError as e:
                # Timeout: The connection is still valid because we use request IDs
                # to correlate responses. The delayed response will be discarded
                # when it arrives and matches a different request ID.
                raise TimeoutException(f"Call timed out after {_timeout}ms") from e

            except (OSError, EOFError, asyncio.IncompleteReadError) as e:
                # Connection is broken - mark it and remove from pool
                conn._broken = True
                raise ConnectionException(f"Connection lost: {e}") from e

            if is_error:
                return self._encoder.decode_type(response_bytes, dict)

            if return_type is not None:
                response = self._encoder.decode_type(response_bytes, return_type)
            else:
                response = self._encoder.decode(response_bytes)

            return response

        finally:
            await self._pool.release(conn)

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
    _request_id: int = 0  # Simple sequence counter for request IDs
    _broken: bool = False  # Mark connection as broken if I/O fails

    @property
    def is_broken(self) -> bool:
        """Check if the connection is broken."""
        # Connection is broken if:
        # 1. Explicitly marked as broken due to I/O error
        # 2. Writer is closed
        # 3. Writer has an exception
        return (
            self._broken
            or self.writer.is_closing()
            or self.writer.get_extra_info("socket") is None
        )

    async def request(self, obj: Any) -> Tuple[bytes, bool]:
        """
        Send a request and wait for the matching response.

        Uses request IDs to match responses with requests, allowing stale
        responses from timed-out requests to be discarded gracefully.

        Returns a tuple of (raw_encoded_payload_bytes, is_error).
        """
        async with self.lock:
            # Increment request ID (wraps at 2^32), increment possible because of lock
            self._request_id = (self._request_id + 1) & 0xFFFFFFFF
            request_id = self._request_id.to_bytes(4, "big")

            await write_frame(self.writer, obj, self.encoder, request_id)

            while True:
                resp_id, resp_payload, is_error = await read_frame(self.reader)
                resp_id_int = int.from_bytes(resp_id, "big")

                if resp_id_int == self._request_id:
                    return resp_payload, is_error
                else:
                    logging.debug(
                        "Discarding stale response (expected %d, got %d)",
                        self._request_id,
                        resp_id_int,
                    )

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

    async def start(self) -> None:
        if self._started:
            return

        # Create all connections concurrently for faster startup
        conns = await asyncio.gather(
            *[self._create_single_connection() for _ in range(self._size)]
        )
        self._all.extend(conns)
        for conn in conns:
            self._q.put_nowait(conn)

        self._started = True
        logging.debug("TCP connection pool initialized with %d connections", self._size)

    async def acquire(self) -> PooledTCPConn:
        # Get a connection from the pool
        return await self._q.get()

    async def release(self, conn: PooledTCPConn) -> None:
        if conn.is_broken:
            logging.debug(
                "Detected broken connection, scheduling replacement in background"
            )
            asyncio.create_task(self._replace_broken_connection_with_backoff(conn))
        else:
            # Connection is healthy, put it back in the pool
            await self._q.put(conn)

    async def _replace_broken_connection_with_backoff(
        self, broken_conn: PooledTCPConn
    ) -> None:
        base_delay = 1  # second
        max_delay = 20  # seconds

        await broken_conn.close()

        attempt = 0
        while True:
            try:
                new_conn = await self._create_single_connection()
                await self._q.put(new_conn)
                logging.debug(
                    "Successfully created replacement connection after %d attempt(s)",
                    attempt + 1,
                )
                return
            except Exception as e:  # pylint: disable=broad-except
                attempt += 1
                delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
                logging.warning(
                    "Failed to create replacement connection (attempt %d), retrying in %.2fs: %s",
                    attempt,
                    delay,
                    e,
                )
                await asyncio.sleep(delay)

    async def _create_single_connection(self) -> PooledTCPConn:
        """Create a single TCP connection."""
        reader, writer = await asyncio.open_connection(self._host, self._port)
        return PooledTCPConn(
            reader=reader,
            writer=writer,
            encoder=self._encoder,
            lock=asyncio.Lock(),
        )

    async def close(self) -> None:
        for c in self._all:
            await c.close()
