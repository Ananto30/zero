import asyncio
import logging
import os
from typing import Optional, Union

import msgpack
import zmq
import zmq.asyncio

from zero.errors import MethodNotFoundException, ZeroException


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
        self._socket: Optional[zmq.Socket] = None

    def _init_serializer(self):
        # msgpack is the default serializer
        if self._serializer == "msgpack":
            self._encode = msgpack.packb
            self._decode = msgpack.unpackb

    def _set_socket_opt(self):
        if self._socket is None:
            raise ZeroException("Socket is not initialized")

        if os.name == "nt":
            # windows need special event loop policy to work with zmq
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

        self._socket.setsockopt(zmq.RCVTIMEO, self._default_timeout)
        self._socket.setsockopt(zmq.SNDTIMEO, self._default_timeout)
        self._socket.setsockopt(zmq.LINGER, 0)  # dont buffer messages


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
        ctx = zmq.Context.instance()
        self._socket: zmq.Socket = ctx.socket(zmq.DEALER)
        self._set_socket_opt()
        self._socket.connect(f"tcp://{self._host}:{self._port}")

    def call(self, rpc_method_name: str, msg: Union[int, float, str, dict, list, tuple, None]):
        """
        Call the rpc method of the ZeroServer.

        @param rpc_method_name:
        Method name should be string. This method should reside on the ZeroServer to get a successful response.

        @param msg:
        For msgpack serializer, msg should be base Python types. Cannot be objects.

        @return:
        Returns the response of ZeroServer's rpc method.
        """
        if self._socket is None:
            self._init_socket()

        try:
            msg = "" if msg is None else msg
            self._socket.send_multipart([rpc_method_name.encode(), self._encode(msg)], zmq.DONTWAIT)
            resp = self._socket.recv()
            decoded_resp = self._decode(resp)

            if isinstance(decoded_resp, dict):
                if "__zerror__method_not_found" in decoded_resp:
                    raise MethodNotFoundException(decoded_resp.get("__zerror__method_not_found"))

            return decoded_resp

        except ZeroException as ze:
            raise ze

        except Exception as e:
            self._socket.close()
            self._init_socket()
            logging.exception(e)


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
        ctx = zmq.asyncio.Context.instance()
        self._socket: zmq.asyncio.Socket = ctx.socket(zmq.DEALER)
        self._set_socket_opt()
        self._socket.connect(f"tcp://{self._host}:{self._port}")

    async def call(self, rpc_method_name: str, msg: Union[int, float, str, dict, list, tuple, None]):
        """
        Call the rpc method of the ZeroServer.

        @param rpc_method_name:
        Method name should be string. This method should reside on the ZeroServer to get a successful response.

        @param msg:
        For msgpack serializer, msg should be base Python types. Cannot be objects.

        @return:
        Returns the response of ZeroServer's rpc method.
        """
        if self._socket is None:
            self._init_async_socket()

        try:
            msg = "" if msg is None else msg
            await self._socket.send_multipart([rpc_method_name.encode(), self._encode(msg)], zmq.DONTWAIT)
            resp = await self._socket.recv()
            decoded_resp = self._decode(resp)

            if isinstance(decoded_resp, dict):
                if "__zerror__method_not_found" in decoded_resp:
                    raise MethodNotFoundException(decoded_resp.get("__zerror__method_not_found"))

            return decoded_resp

        except ZeroException as ze:
            raise ze

        except Exception as e:
            self._socket.close()
            self._init_async_socket()
            logging.exception(e)
