import asyncio
import logging
import os
from typing import Any, Dict, Optional, Union

import msgpack
import zmq
import zmq.asyncio

from .error import ConnectionException, MethodNotFoundException, TimeoutException, ZeroException
from .util import current_time_ms, unique_id


class _BaseClient:
    def __init__(
        self,
        host: str,
        port: int,
        default_timeout: int = 2000,
    ):
        self._host = host
        self._port = port
        self._default_timeout = default_timeout
        self._serializer = "msgpack"
        self._init_serializer()
        self._socket: zmq.Socket = None  # type: ignore
        self._poller: zmq.Poller = None  # type: ignore

    def _init_serializer(self):
        # msgpack is the default serializer
        if self._serializer == "msgpack":
            self._encode = msgpack.packb
            self._decode = msgpack.unpackb

    def _set_socket_opt(self):
        self._set_default_timeout()
        self._socket.setsockopt(zmq.LINGER, 0)  # dont buffer messages

    def _set_socket_timeout(self, timeout):
        self._socket.setsockopt(zmq.RCVTIMEO, timeout)
        self._socket.setsockopt(zmq.SNDTIMEO, timeout)

    def _set_default_timeout(self):
        self._set_socket_timeout(self._default_timeout)

    def close(self):
        self._socket.close() if self._socket else None


class ZeroClient(_BaseClient):
    def __init__(
        self,
        host: str,
        port: int,
        default_timeout: int = 2000,
    ):
        """
        ZeroClient provides the client interface for calling the ZeroServer.

        @param host:
        Host of the ZeroServer.

        @param port:
        Port of the ZeroServer.

        @param default_timeout:
        Default timeout for each call. In milliseconds.
        """
        super().__init__(host, port, default_timeout)

    def _init_socket(self):
        ctx = zmq.Context.instance()  # TODO check if ctx is thread safe

        self._socket: zmq.Socket = ctx.socket(zmq.DEALER)
        self._set_socket_opt()
        self._socket.connect(f"tcp://{self._host}:{self._port}")

        self._poller = zmq.Poller()
        self._poller.register(self._socket, zmq.POLLIN)

    def _ensure_conntected(self):
        if self._socket is not None:
            return

        self._init_socket()
        self.try_connect()

    def try_connect(self):
        try:
            frames = [unique_id(), "connect", ""]
            self._socket.send(self._encode(frames))
            _, resp_data = self._decode(self._socket.recv())
            if resp_data != "connected":
                raise ConnectionException(f"Cannot connect to server at {self._host}:{self._port}")

            logging.info(f"Connected to server at {self._host}:{self._port}")

        except zmq.error.Again:
            raise ConnectionException(f"Cannot connect to server at {self._host}:{self._port}")

    def call(
        self,
        rpc_method_name: str,
        msg: Union[int, float, str, dict, list, tuple, None],
        timeout: Optional[int] = None,
    ) -> Any:
        """
        Call the rpc method of the ZeroServer.

        @param rpc_method_name:
        Method name should be string. This method should reside on the ZeroServer to get a successful response.

        @param msg:
        For msgpack serializer, msg should be base Python types. Cannot be objects.

        @param timeout:
        Timeout for the call. In milliseconds.

        @return:
        Returns the response of ZeroServer's rpc method.
        """
        self._ensure_conntected()

        _timeout = self._default_timeout if timeout is None else timeout

        def _poll_data():
            socks = dict(self._poller.poll(_timeout))
            if self._socket not in socks:
                raise TimeoutException(f"Timeout while sending message at {self._host}:{self._port}")

            resp_id, resp_data = self._decode(self._socket.recv())
            if isinstance(resp_data, dict) and "__zerror__method_not_found" in resp_data:
                raise MethodNotFoundException(resp_data.get("__zerror__method_not_found"))
            return resp_id, resp_data

        def _call():
            req_id = unique_id()
            expire_at = current_time_ms() + _timeout

            frames = [req_id, rpc_method_name, "" if msg is None else msg]
            self._socket.send(self._encode(frames), zmq.DONTWAIT)

            resp_id, resp_data = _poll_data()
            while resp_id != req_id:
                if current_time_ms() > expire_at:
                    raise TimeoutException(f"Timeout while waiting for response at {self._host}:{self._port}")
                resp_id, resp_data = _poll_data()

            return resp_data

        try:
            return _call()
        except ZeroException:
            raise
        # non-blocking mode was requested and the message cannot be sent at the moment
        except zmq.error.Again:
            raise ConnectionException(f"Connection error at {self._host}:{self._port}")
        except Exception as e:
            self.close()
            self._init_socket()
            logging.exception(e)
            raise


class AsyncZeroClient(_BaseClient):
    def __init__(
        self,
        host: str,
        port: int,
        default_timeout: int = 2000,
    ):
        """
        AsyncZeroClient provides the asynchronous client interface for calling the ZeroServer.
        You can use Python's async/await with this client.
        Naturally async client is faster.

        @param host:
        Host of the ZeroServer.

        @param port:
        Port of the ZeroServer.

        @param default_timeout:
        Default timeout for each call. In milliseconds.
        """
        super().__init__(host, port, default_timeout)

    def _init_async_socket(self):
        if os.name == "nt":
            # windows need special event loop policy to work with zmq
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

        ctx = zmq.asyncio.Context.instance()  # TODO check if ctx is thread safe

        self._socket: zmq.asyncio.Socket = ctx.socket(zmq.DEALER)
        self._set_socket_opt()
        self._socket.connect(f"tcp://{self._host}:{self._port}")

        self._poller: zmq.asyncio.Poller = zmq.asyncio.Poller()
        self._poller.register(self._socket, zmq.POLLIN)

        self.__resps: Dict[str, Any] = {}

    async def _ensure_connected(self):
        if self._socket is not None:
            return

        self._init_async_socket()
        await self.try_connect()

    async def try_connect(self):
        try:
            frames = [unique_id(), "connect", ""]
            await self._socket.send(self._encode(frames))
            _, resp_data = self._decode(await self._socket.recv())
            if resp_data != "connected":
                raise ConnectionException(f"Cannot connect to server at {self._host}:{self._port}")

            logging.info(f"Connected to server at {self._host}:{self._port}")

        except zmq.error.Again:
            raise ConnectionException(f"Cannot connect to server at {self._host}:{self._port}")

    async def call(
        self,
        rpc_method_name: str,
        msg: Union[int, float, str, dict, list, tuple, None],
        timeout: Optional[int] = None,
    ) -> Any:
        """
        Call the rpc method of the ZeroServer.

        @param rpc_method_name:
        Method name should be string. This method should reside on the ZeroServer to get a successful response.

        @param msg:
        For msgpack serializer, msg should be base Python types. Cannot be objects.

        @param timeout:
        Timeout for the call. In milliseconds.

        @return:
        Returns the response of ZeroServer's rpc method.
        """
        await self._ensure_connected()

        _timeout = self._default_timeout if timeout is None else timeout

        async def _poll_data():
            # TODO async has issue with poller, after 3-4 calls, it returns empty
            # socks = await self._poller.poll(_timeout)
            # print("poll", socks)
            # if self._socket not in dict(socks):
            #     raise TimeoutException(f"Timeout while sending message at {self._host}:{self._port}")

            resp = await self._socket.recv()
            resp_id, resp_data = self._decode(resp)
            self.__resps[resp_id] = resp_data

        async def _call():
            req_id = unique_id()
            expire_at = current_time_ms() + _timeout

            frames = [req_id, rpc_method_name, "" if msg is None else msg]
            await self._socket.send(self._encode(frames))

            await _poll_data()

            while req_id not in self.__resps and current_time_ms() < expire_at:
                await asyncio.sleep(1e-4)

            # while req_id not in self.__resps and current_time_ms() <= expire_at:
            #     try:
            #         await _poll_data()
            #     except zmq.error.Again:
            #         pass

            if current_time_ms() > expire_at:
                raise TimeoutException(f"Timeout while waiting for response at {self._host}:{self._port}")

            resp_data = self.__resps.pop(req_id)

            if isinstance(resp_data, dict) and "__zerror__method_not_found" in resp_data:
                raise MethodNotFoundException(resp_data.get("__zerror__method_not_found"))

            return resp_data

        try:
            return await _call()
        except ZeroException:
            raise
        # non-blocking mode was requested and the message cannot be sent at the moment
        except zmq.error.Again:
            raise ConnectionException(f"Connection error at {self._host}:{self._port}")
        except Exception as e:
            self.close()
            self._init_async_socket()
            logging.exception(e)
            raise
