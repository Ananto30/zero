import logging
import threading
from typing import Dict, Optional, Type, TypeVar

from zero import config
from zero.encoder import Encoder
from zero.encoder.msgspc import MsgspecEncoder
from zero.utils.type_util import AllowedType
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
        default_timeout: int,
        encoder: Encoder,
    ):
        self._encoder = encoder or MsgspecEncoder()

        self.client_pool = ZMQClientPool(address, default_timeout)

    def call(
        self,
        rpc_func_name: str,
        msg: AllowedType,
        timeout: Optional[int] = None,
        return_type: Optional[Type[T]] = None,
    ) -> T:
        zmqc = self.client_pool.get()

        # make function name exactly 80 bytes
        func_name_bytes = rpc_func_name.ljust(80).encode()
        msg_bytes = b"" if msg is None else self._encoder.encode(msg)

        resp_data_bytes = zmqc.request(func_name_bytes + msg_bytes, timeout)

        return (
            self._encoder.decode(resp_data_bytes)
            if return_type is None
            else self._encoder.decode_type(resp_data_bytes, return_type)
        )

    def close(self):
        self.client_pool.close()


class AsyncZMQClient:
    def __init__(
        self,
        address: str,
        default_timeout: int,
        encoder: Encoder,
    ):
        self._encoder = encoder

        self.client_pool = AsyncZMQClientPool(address, default_timeout)

    async def call(
        self,
        rpc_func_name: str,
        msg: AllowedType,
        timeout: Optional[int] = None,
        return_type: Optional[Type[T]] = None,
    ) -> T:
        zmqc = await self.client_pool.get()

        # make function name exactly 80 bytes
        func_name_bytes = rpc_func_name.ljust(80).encode()
        msg_bytes = b"" if msg is None else self._encoder.encode(msg)

        resp_data_bytes = await zmqc.request(func_name_bytes + msg_bytes, timeout)

        return (
            self._encoder.decode(resp_data_bytes)
            if return_type is None
            else self._encoder.decode_type(resp_data_bytes, return_type)
        )

    def close(self):
        self.client_pool.close()


class ZMQClientPool:
    """
    Connections are based on different threads and processes.
    Each time a call is made it tries to get the connection from the pool,
    based on the thread/process id.
    If the connection is not available, it creates a new connection and stores it in the pool.
    """

    __slots__ = ["_pool", "_address", "_timeout"]

    def __init__(self, address: str, timeout: int):
        self._pool: Dict[int, ZeroMQClient] = {}
        self._address = address
        self._timeout = timeout

    def get(self) -> ZeroMQClient:
        thread_id = threading.get_ident()
        if thread_id not in self._pool:
            logging.debug("No connection found in current thread, creating new one")
            self._pool[thread_id] = get_client(config.ZEROMQ_PATTERN, self._timeout)
            self._pool[thread_id].connect(self._address)
        return self._pool[thread_id]

    def close(self):
        for client in self._pool.values():
            client.close()
        self._pool = {}


class AsyncZMQClientPool:
    """
    Connections are based on different threads and processes.
    Each time a call is made it tries to get the connection from the pool,
    based on the thread/process id.
    If the connection is not available, it creates a new connection and stores it in the pool.
    """

    __slots__ = ["_pool", "_address", "_timeout"]

    def __init__(self, address: str, timeout: int):
        self._pool: Dict[int, AsyncZeroMQClient] = {}
        self._address = address
        self._timeout = timeout

    async def get(self) -> AsyncZeroMQClient:
        thread_id = threading.get_ident()
        if thread_id not in self._pool:
            logging.debug("No connection found in current thread, creating new one")
            self._pool[thread_id] = get_async_client(
                config.ZEROMQ_PATTERN, self._timeout
            )
            await self._pool[thread_id].connect(self._address)
        return self._pool[thread_id]

    def close(self):
        for client in self._pool.values():
            client.close()
        self._pool = {}
