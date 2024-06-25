import asyncio
import logging
import threading
from typing import Any, Dict, Optional, Type, TypeVar, Union

from zero import config
from zero.encoder import Encoder, get_encoder
from zero.error import TimeoutException
from zero.utils import util
from zero.zeromq_patterns import (
    AsyncZeroMQClient,
    ZeroMQClient,
    get_async_client,
    get_client,
)

T = TypeVar("T")


class ZMQClient:
    def __init__(
        self,
        address: str,
        default_timeout: int = 2000,
        encoder: Optional[Encoder] = None,
    ):
        self._address = address
        self._default_timeout = default_timeout
        self._encoder = encoder or get_encoder(config.ENCODER)

        self.client_pool = ZeroMQClientPool(
            self._address,
            self._default_timeout,
            self._encoder,
        )

    def call(
        self,
        rpc_func_name: str,
        msg: Union[int, float, str, dict, list, tuple, None],
        timeout: Optional[int] = None,
        return_type: Optional[Type[T]] = None,
    ) -> T:
        zmqc = self.client_pool.get()

        _timeout = self._default_timeout if timeout is None else timeout

        def _poll_data():
            # TODO poll is slow, need to find a better way
            if not zmqc.poll(_timeout):
                raise TimeoutException(
                    f"Timeout while sending message at {self._address}"
                )

            rcv_data = zmqc.recv()

            # first 32 bytes as response id
            resp_id = rcv_data[:32].decode()

            # the rest is response data
            resp_data_encoded = rcv_data[32:]
            resp_data = (
                self._encoder.decode(resp_data_encoded)
                if return_type is None
                else self._encoder.decode_type(resp_data_encoded, return_type)
            )

            return resp_id, resp_data

        req_id = util.unique_id()

        # function name exactly 120 bytes
        func_name_bytes = rpc_func_name.ljust(120).encode()

        msg_bytes = b"" if msg is None else self._encoder.encode(msg)
        zmqc.send(req_id.encode() + func_name_bytes + msg_bytes)

        resp_id, resp_data = None, None
        # as the client is synchronous, we know that the response will be available any next poll
        # we try to get the response until timeout because a previous call might be timed out
        # and the response is still in the socket,
        # so we poll until we get the response for this call
        while resp_id != req_id:
            resp_id, resp_data = _poll_data()

        return resp_data  # type: ignore

    def close(self):
        self.client_pool.close()


class AsyncZMQClient:
    def __init__(
        self,
        address: str,
        default_timeout: int = 2000,
        encoder: Optional[Encoder] = None,
    ):
        self._address = address
        self._default_timeout = default_timeout
        self._encoder = encoder or get_encoder(config.ENCODER)
        self._resp_map: Dict[str, Any] = {}

        self.client_pool = AsyncZeroMQClientPool(
            self._address,
            self._default_timeout,
            self._encoder,
        )

    async def call(
        self,
        rpc_func_name: str,
        msg: Union[int, float, str, dict, list, tuple, None],
        timeout: Optional[int] = None,
        return_type: Optional[Type[T]] = None,
    ) -> T:
        zmqc = await self.client_pool.get()

        _timeout = self._default_timeout if timeout is None else timeout
        expire_at = util.current_time_us() + (_timeout * 1000)

        async def _poll_data():
            # TODO async has issue with poller, after 3-4 calls, it returns empty
            # if not await zmqc.poll(_timeout):
            #     raise TimeoutException(f"Timeout while sending message at {self._address}")

            # first 32 bytes as response id
            resp = await zmqc.recv()
            resp_id = resp[:32].decode()

            # the rest is response data
            resp_data_encoded = resp[32:]
            resp_data = (
                self._encoder.decode(resp_data_encoded)
                if return_type is None
                else self._encoder.decode_type(resp_data_encoded, return_type)
            )
            self._resp_map[resp_id] = resp_data

            # TODO try to use pipe instead of sleep
            # await self.peer1.send(b"")

        req_id = util.unique_id()

        # function name exactly 120 bytes
        func_name_bytes = rpc_func_name.ljust(120).encode()

        msg_bytes = b"" if msg is None else self._encoder.encode(msg)
        await zmqc.send(req_id.encode() + func_name_bytes + msg_bytes)

        # every request poll the data, so whenever a response comes, it will be stored in __resps
        # dont need to poll again in the while loop
        await _poll_data()

        while req_id not in self._resp_map and util.current_time_us() <= expire_at:
            # TODO the problem with the zpipe is that we can miss some response
            # when we come to this line
            # await self.peer2.recv()
            await asyncio.sleep(1e-6)

        if util.current_time_us() > expire_at:
            raise TimeoutException(
                f"Timeout while waiting for response at {self._address}"
            )

        resp_data = self._resp_map.pop(req_id)

        return resp_data

    def close(self):
        self.client_pool.close()
        self._resp_map = {}


class ZeroMQClientPool:
    """
    Connections are based on different threads and processes.
    Each time a call is made it tries to get the connection from the pool,
    based on the thread/process id.
    If the connection is not available, it creates a new connection and stores it in the pool.
    """

    __slots__ = ["_pool", "_address", "_timeout", "_encoder"]

    def __init__(
        self, address: str, timeout: int = 2000, encoder: Optional[Encoder] = None
    ):
        self._pool: Dict[int, ZeroMQClient] = {}
        self._address = address
        self._timeout = timeout
        self._encoder = encoder or get_encoder(config.ENCODER)

    def get(self) -> ZeroMQClient:
        thread_id = threading.get_ident()
        if thread_id not in self._pool:
            logging.debug("No connection found in current thread, creating new one")
            self._pool[thread_id] = get_client(config.ZEROMQ_PATTERN, self._timeout)
            self._pool[thread_id].connect(self._address)
            self._try_connect_ping(self._pool[thread_id])
        return self._pool[thread_id]

    def _try_connect_ping(self, client: ZeroMQClient):
        client.send(util.unique_id().encode() + b"connect" + b"")
        client.recv()
        logging.info("Connected to server at %s", self._address)

    def close(self):
        for client in self._pool.values():
            client.close()
        self._pool = {}


class AsyncZeroMQClientPool:
    """
    Connections are based on different threads and processes.
    Each time a call is made it tries to get the connection from the pool,
    based on the thread/process id.
    If the connection is not available, it creates a new connection and stores it in the pool.
    """

    __slots__ = ["_pool", "_address", "_timeout", "_encoder"]

    def __init__(
        self, address: str, timeout: int = 2000, encoder: Optional[Encoder] = None
    ):
        self._pool: Dict[int, AsyncZeroMQClient] = {}
        self._address = address
        self._timeout = timeout
        self._encoder = encoder or get_encoder(config.ENCODER)

    async def get(self) -> AsyncZeroMQClient:
        thread_id = threading.get_ident()
        if thread_id not in self._pool:
            logging.debug("No connection found in current thread, creating new one")
            self._pool[thread_id] = get_async_client(
                config.ZEROMQ_PATTERN, self._timeout
            )
            self._pool[thread_id].connect(self._address)
            await self._try_connect_ping(self._pool[thread_id])
        return self._pool[thread_id]

    async def _try_connect_ping(self, client: AsyncZeroMQClient):
        await client.send(util.unique_id().encode() + b"connect" + b"")
        await client.recv()
        logging.info("Connected to server at %s", self._address)

    def close(self):
        for client in self._pool.values():
            client.close()
        self._pool = {}
