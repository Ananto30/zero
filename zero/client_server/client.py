import asyncio
import logging
from typing import Any, Dict, Optional, Union

import zero.config as config
from zero.encoder import Encoder, get_encoder
from zero.error import MethodNotFoundException, TimeoutException
from zero.utils import util
from zero.zero_mq import AsyncZeroMQClient, ZeroMQClient, get_async_client, get_client
from zero.zero_mq.helpers import zpipe_async


class ZeroClient:
    def __init__(
        self,
        host: str,
        port: int,
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

        Parameters
        ----------
        host: str
            Host of the ZeroServer.

        port: int
            Port of the ZeroServer.

        default_timeout: int
            Default timeout for the ZeroClient for all calls.
            Default is 2000 ms.

        encoder: Optional[Encoder]
            Encoder to encode/decode messages from/to client.
            Default is msgpack.
            If any other encoder is used, the server should use the same encoder.
            Implement custom encoder by inheriting from `zero.encoder.Encoder`.
        """
        self._address = f"tcp://{host}:{port}"
        self._default_timeout = default_timeout
        self.encdr = encoder or get_encoder(config.ENCODER)

        self.zmqc: ZeroMQClient = None  # type: ignore

    def call(
        self,
        rpc_func_name: str,
        msg: Union[int, float, str, dict, list, tuple, None],
        timeout: Optional[int] = None,
    ) -> Any:
        """
        Call the rpc function resides on the ZeroServer.

        Parameters
        ----------
        rpc_func_name: str
            Function name should be string. This funtion should reside on the ZeroServer to get a successful response.

        msg: Union[int, float, str, dict, list, tuple, None]
            The only argument of the rpc function. This should be of the same type as the rpc function's argument.

        timeout: Optional[int]
            Timeout for the call. In milliseconds.
            Default is 2000 milliseconds.

        Returns
        -------
        Any
            The return value of the rpc function.

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
        self._ensure_conntected()

        _timeout = self._default_timeout if timeout is None else timeout

        def _poll_data():
            if not self.zmqc.poll(_timeout):
                raise TimeoutException(f"Timeout while sending message at {self._address}")

            resp_id, resp_data = self.encdr.decode(self.zmqc.recv())
            return resp_id, resp_data

        req_id = util.unique_id()
        frames = [req_id, rpc_func_name, "" if msg is None else msg]
        self.zmqc.send(self.encdr.encode(frames))

        resp_id, resp_data = None, None
        # as the client is synchronous, we know that the response will be available any next poll
        # we try to get the response until timeout because a previous call might be timed out
        # and the response is still in the socket, so we poll until we get the response for this call
        while resp_id != req_id:
            resp_id, resp_data = _poll_data()

        if isinstance(resp_data, dict) and "__zerror__function_not_found" in resp_data:
            raise MethodNotFoundException(resp_data.get("__zerror__function_not_found"))

        return resp_data

    def close(self):
        if self.zmqc is not None:
            self.zmqc.close()
            self.zmqc = None  # type: ignore

    def _ensure_conntected(self):
        if self.zmqc is not None:
            return

        self._init()
        self._try_connect()

    def _init(self):
        self.zmqc = get_client(config.ZEROMQ_PATTERN, self._default_timeout)
        self.zmqc.connect(self._address)

    def _try_connect(self):
        frames = [util.unique_id(), "connect", ""]
        self.zmqc.send(self.encdr.encode(frames))
        self.encdr.decode(self.zmqc.recv())
        logging.info(f"Connected to server at {self._address}")


class AsyncZeroClient:
    def __init__(
        self,
        host: str,
        port: int,
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


        Parameters
        ----------
        host: str
            Host of the ZeroServer.

        port: int
            Port of the ZeroServer.

        default_timeout: int
            Default timeout for the AsyncZeroClient for all calls.
            Default is 2000 ms.

        encoder: Optional[Encoder]
            Encoder to encode/decode messages from/to client.
            Default is msgpack.
            If any other encoder is used, the server should use the same encoder.
            Implement custom encoder by inheriting from `zero.encoder.Encoder`.
        """
        self._address = f"tcp://{host}:{port}"
        self._default_timeout = default_timeout
        self._encoder = encoder or get_encoder(config.ENCODER)

        self.zmqc: AsyncZeroMQClient = None  # type: ignore

    async def call(
        self,
        rpc_func_name: str,
        msg: Union[int, float, str, dict, list, tuple, None],
        timeout: Optional[int] = None,
    ) -> Any:
        """
        Call the rpc function resides on the ZeroServer.

        Parameters
        ----------
        rpc_func_name: str
            Function name should be string. This funtion should reside on the ZeroServer to get a successful response.

        msg: Union[int, float, str, dict, list, tuple, None]
            The only argument of the rpc function. This should be of the same type as the rpc function's argument.

        timeout: Optional[int]
            Timeout for the call. In milliseconds.
            Default is 2000 milliseconds.

        Returns
        -------
        Any
            The return value of the rpc function.

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
        await self._ensure_connected()

        _timeout = self._default_timeout if timeout is None else timeout
        expire_at = util.current_time_us() + (_timeout * 1000)

        async def _poll_data():
            # TODO async has issue with poller, after 3-4 calls, it returns empty
            # if not await self.zmq_client.poll(_timeout):
            #     raise TimeoutException(f"Timeout while sending message at {self._address}")

            resp = await self.zmqc.recv()
            resp_id, resp_data = self._encoder.decode(resp)
            self._resp_map[resp_id] = resp_data

            # TODO try to use pipe instead of sleep
            # await self.peer1.send(b"")

        req_id = util.unique_id()
        frames = [req_id, rpc_func_name, "" if msg is None else msg]
        await self.zmqc.send(self._encoder.encode(frames))

        # every request poll the data, so whenever a response comes, it will be stored in __resps
        # dont need to poll again in the while loop
        await _poll_data()

        while req_id not in self._resp_map and util.current_time_us() <= expire_at:
            # TODO the problem with the pipe is that we can miss some response
            # when we come to this line
            # await self.peer2.recv()
            await asyncio.sleep(1e-6)

        if util.current_time_us() > expire_at:
            raise TimeoutException(f"Timeout while waiting for response at {self._address}")

        resp_data = self._resp_map.pop(req_id)

        if isinstance(resp_data, dict) and "__zerror__function_not_found" in resp_data:
            raise MethodNotFoundException(resp_data.get("__zerror__function_not_found"))

        return resp_data

    def close(self):
        if self.zmqc is not None:
            self.zmqc.close()
            self.zmqc = None  # type: ignore
            self._resp_map = {}

    async def _ensure_connected(self):
        if self.zmqc is not None:
            return

        self._init()
        await self._try_connect()

    def _init(self):
        self.zmqc = get_async_client(config.ZEROMQ_PATTERN, self._default_timeout)
        self.zmqc.connect(self._address)

        self._resp_map: Dict[str, Any] = {}

        self.peer1, self.peer2 = zpipe_async(self.zmqc.context, 10000)
        # TODO try to use pipe instead of sleep
        # asyncio.create_task(self._poll_data())

    async def _try_connect(self):
        frames = [util.unique_id(), "connect", ""]
        await self.zmqc.send(self._encoder.encode(frames))
        self._encoder.decode(await self.zmqc.recv())
        logging.info(f"Connected to server at {self._address}")

    async def _poll_data(self):  # pragma: no cover
        while True:
            try:
                if not await self.zmqc.poll(self._default_timeout):
                    continue

                frames = await self.zmqc.recv()
                resp_id, data = self._encoder.decode(frames)
                self._resp_map[resp_id] = data
                await self.peer1.send(b"")
            except Exception as e:
                logging.error(f"Error while polling data: {e}")
