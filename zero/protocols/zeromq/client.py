import asyncio
import logging
import threading
from typing import Any, Dict, Optional, Tuple, Type, TypeVar, Union

from zero import config
from zero.encoder import Encoder, get_encoder
from zero.error import TimeoutException
from zero.utils import util
from zero.zero_mq import AsyncZeroMQClient, ZeroMQClient, get_async_client, get_client

T = TypeVar("T")


class ZMQClient:
    def __init__(
        self,
        address: str,
        default_timeout: int = 2000,
        encoder: Optional[Encoder] = None,
    ):
        """
        ZeroClient provides the client interface for calling the ZeroServer.

        Zero use tcp protocol for communication.
        So a connection needs to be established to make a call.
        The connection creation is done lazily.
        So the first call will take some time to establish the connection.
        If the connection is dropped the client might timeout.
        But in the next call the connection will be re-established.

        For different threads/processes, different connections are created.

        Parameters
        ----------
        host: str
            Host of the ZeroServer.

        port: int
            Port of the ZeroServer.

        default_timeout: int
            Default timeout for all calls. Default is 2000 ms.

        encoder: Optional[Encoder]
            Encoder to encode/decode messages from/to client.
            Default is msgspec.
            If any other encoder is used, make sure the server should use the same encoder.
            Implement custom encoder by inheriting from `zero.encoder.Encoder`.
        """
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
        """
        Call the rpc function resides on the ZeroServer.

        Parameters
        ----------
        rpc_func_name: str
            Function name should be string.
            This funtion should reside on the ZeroServer to get a successful response.

        msg: Union[int, float, str, dict, list, tuple, None]
            The only argument of the rpc function.
            This should be of the same type as the rpc function's argument.

        timeout: Optional[int]
            Timeout for the call. In milliseconds.
            Default is 2000 milliseconds.

        return_type: Optional[Type[T]]
            The return type of the rpc function.
            If return_type is set, the response will be parsed to the return_type.

        Returns
        -------
        T
            The return value of the rpc function.
            If return_type is set, the response will be parsed to the return_type.

        Raises
        ------
        TimeoutException
            If the call times out or the connection is dropped.

        MethodNotFoundException
            If the rpc function is not found on the ZeroServer.

        ConnectionException
            If zeromq connection is not established.
            Or zeromq cannot send the message to the server.
            Or zeromq cannot receive the response from the server.
            Mainly represents zmq.error.Again exception.
        """
        zmqc = self.client_pool.get()

        _timeout = self._default_timeout if timeout is None else timeout

        def _poll_data():
            # TODO poll is slow, need to find a better way
            if not zmqc.poll(_timeout):
                raise TimeoutException(
                    f"Timeout while sending message at {self._address}"
                )

            resp_id, resp_data = (
                self._encoder.decode(zmqc.recv())
                if return_type is None
                else self._encoder.decode_type(zmqc.recv(), Tuple[str, return_type])
            )
            return resp_id, resp_data

        req_id = util.unique_id()
        frames = [req_id, rpc_func_name, "" if msg is None else msg]
        zmqc.send(self._encoder.encode(frames))

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
        """
        AsyncZeroClient provides the asynchronous client interface for calling the ZeroServer.
        Python's async/await can be used to make the calls.
        Naturally async client is faster.

        Zero use tcp protocol for communication.
        So a connection needs to be established to make a call.
        The connection creation is done lazily.
        So the first call will take some time to establish the connection.
        If the connection is dropped the client might timeout.
        But in the next call the connection will be re-established.

        For different threads/processes, different connections are created.

        Parameters
        ----------
        host: str
            Host of the ZeroServer.

        port: int
            Port of the ZeroServer.

        default_timeout: int
            Default timeout for all calls. Default is 2000 ms.

        encoder: Optional[Encoder]
            Encoder to encode/decode messages from/to client.
            Default is msgspec.
            If any other encoder is used, the server should use the same encoder.
            Implement custom encoder by inheriting from `zero.encoder.Encoder`.
        """
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
        """
        Call the rpc function resides on the ZeroServer.

        Parameters
        ----------
        rpc_func_name: str
            Function name should be string.
            This funtion should reside on the ZeroServer to get a successful response.

        msg: Union[int, float, str, dict, list, tuple, None]
            The only argument of the rpc function.
            This should be of the same type as the rpc function's argument.

        timeout: Optional[int]
            Timeout for the call. In milliseconds.
            Default is 2000 milliseconds.

        return_type: Optional[Type[T]]
            The return type of the rpc function.
            If return_type is set, the response will be parsed to the return_type.

        Returns
        -------
        T
            The return value of the rpc function.
            If return_type is set, the response will be parsed to the return_type.

        Raises
        ------
        TimeoutException
            If the call times out or the connection is dropped.

        MethodNotFoundException
            If the rpc function is not found on the ZeroServer.

        ConnectionException
            If zeromq connection is not established.
            Or zeromq cannot send the message to the server.
            Or zeromq cannot receive the response from the server.
            Mainly represents zmq.error.Again exception.
        """
        zmqc = await self.client_pool.get()

        _timeout = self._default_timeout if timeout is None else timeout
        expire_at = util.current_time_us() + (_timeout * 1000)

        async def _poll_data():
            # TODO async has issue with poller, after 3-4 calls, it returns empty
            # if not await zmqc.poll(_timeout):
            #     raise TimeoutException(f"Timeout while sending message at {self._address}")

            resp = await zmqc.recv()
            resp_id, resp_data = (
                self._encoder.decode(resp)
                if return_type is None
                else self._encoder.decode_type(resp, Tuple[str, return_type])
            )
            self._resp_map[resp_id] = resp_data

            # TODO try to use pipe instead of sleep
            # await self.peer1.send(b"")

        req_id = util.unique_id()
        frames = [req_id, rpc_func_name, "" if msg is None else msg]
        await zmqc.send(self._encoder.encode(frames))

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
        frames = [util.unique_id(), "connect", ""]
        client.send(self._encoder.encode(frames))
        self._encoder.decode(client.recv())
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
        frames = [util.unique_id(), "connect", ""]
        await client.send(self._encoder.encode(frames))
        self._encoder.decode(await client.recv())
        logging.info("Connected to server at %s", self._address)

    def close(self):
        for client in self._pool.values():
            client.close()
        self._pool = {}
