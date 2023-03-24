import asyncio
import logging
import os
from typing import Optional, Union

import msgpack
import zmq
import zmq.asyncio

from zero.error import ConnectionException, MethodNotFoundException, TimeoutException, ZeroException


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
        self._socket.close()


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

    def call(
        self,
        rpc_method_name: str,
        msg: Union[int, float, str, dict, list, tuple, None],
        timeout: Optional[int] = None,
    ):
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

        if self._socket is None:
            self._init_socket()

        _timeout = self._default_timeout if timeout is None else timeout

        def _call():
            req = "" if msg is None else msg
            self._socket.send_multipart(
                [rpc_method_name.encode(), self._encode(req)],
                zmq.DONTWAIT,
            )

            items = dict(self._poller.poll(_timeout))

            if self._socket in items:
                resp = self._socket.recv()
                decoded_resp = self._decode(resp)
                if isinstance(decoded_resp, dict):
                    if "__zerror__method_not_found" in decoded_resp:
                        raise MethodNotFoundException(decoded_resp.get("__zerror__method_not_found"))
                return decoded_resp

            raise TimeoutException(f"Timeout while sending message at {self._host}:{self._port}")

        try:
            return _call()

        # non-blocking mode was requested and the message cannot be sent at the moment
        except zmq.error.Again:
            raise ConnectionException(f"Connection error at {self._host}:{self._port}")

        except Exception as e:
            self._socket.close()
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

        ctx = zmq.asyncio.Context.instance()

        self._socket: zmq.asyncio.Socket = ctx.socket(zmq.DEALER)
        self._set_socket_opt()
        self._socket.connect(f"tcp://{self._host}:{self._port}")

        self._poller: zmq.asyncio.Poller = zmq.asyncio.Poller()
        self._poller.register(self._socket, zmq.POLLIN)

    async def call(
        self,
        rpc_method_name: str,
        msg: Union[int, float, str, dict, list, tuple, None],
        timeout: Optional[int] = None,
    ):
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
        if self._socket is None:
            self._init_async_socket()

        _timeout = self._default_timeout if timeout is None else timeout

        async def _call():
            req = "" if msg is None else msg
            await self._socket.send_multipart(
                [rpc_method_name.encode(), self._encode(req)],
                zmq.DONTWAIT,
            )

            items = await self._poller.poll(_timeout)
            items = dict(items)

            if self._socket in items:
                resp = await self._socket.recv()
                # return resp
                decoded_resp = self._decode(resp)
                if isinstance(decoded_resp, dict):
                    if "__zerror__method_not_found" in decoded_resp:
                        raise MethodNotFoundException(decoded_resp.get("__zerror__method_not_found"))
                return decoded_resp
            
            raise TimeoutException(f"Timeout while sending message at {self._host}:{self._port}")

        try:
            return await _call()

        # non-blocking mode was requested and the message cannot be sent at the moment
        except zmq.error.Again:
            raise ConnectionException(f"Connection error at {self._host}:{self._port}")

        except Exception as e:
            self._socket.close()
            self._init_async_socket()
            logging.exception(e)
            raise
