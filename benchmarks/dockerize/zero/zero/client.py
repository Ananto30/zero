import logging
from typing import Union

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

    def _init_serializer(self):
        # msgpack is the default serializer
        if self._serializer == "msgpack":
            self._encode = msgpack.packb
            self._decode = msgpack.unpackb

    def _set_socket_opt(self):
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
        self._init_socket()

    def _init_socket(self):
        self._ctx = zmq.Context()
        self._socket: zmq.Socket = self._ctx.socket(zmq.REQ)
        # self._set_socket_opt()
        self._socket.connect(f"tcp://{self._host}:{self._port}")
        
        # context = zmq.Context()
        # client = context.socket(zmq.REQ)
        # client.connect(f"tcp://{self._host}:{self._port}")

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
        try:
            msg = "" if msg is None else msg
            # request = str(msg).encode()
            # client.send(request)
            self._socket.send_multipart([rpc_method_name.encode(), self._encode(msg)], zmq.DONTWAIT)
            retries_left = 3
            while True:
                if (self._socket.poll(self._default_timeout) & zmq.POLLIN) != 0:
                    reply = self._socket.recv()
                    return self._decode(reply)
                retries_left -= 1
                if retries_left == 0:
                    self._ctx.destroy(linger=0)
                    self._socket.close()
                    raise ConnectionError("[client] Unable to reach the server")
                logging.warning("[client] No response from server")
                # Socket is confused. Close and remove it.
                self._socket.setsockopt(zmq.LINGER, 0)
                self._socket.close()
                logging.warning("[client] Reconnecting to server…")
                # Create new connection
                self._socket = self._ctx.socket(zmq.REQ)
                self._socket.connect(f"tcp://{self._host}:{self._port}")
                logging.warning(f"[client] Resending ({msg})")
                self._socket.send_multipart([rpc_method_name.encode(), self._encode(msg)], zmq.DONTWAIT)

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
        self._init_async_socket()

    def _init_async_socket(self):
        ctx = zmq.asyncio.Context()
        self._socket: zmq.Socket = ctx.socket(zmq.DEALER)
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
        try:
            msg = "" if msg is None else msg
            # request = str(msg).encode()
            # client.send(request)
            await self._socket.send_multipart([rpc_method_name.encode(), self._encode(msg)], zmq.DONTWAIT)
            retries_left = 3
            while True:
                if (self._socket.poll(self._default_timeout) & zmq.POLLIN) != 0:
                    reply = await self._socket.recv()
                    return self._decode(reply)
                retries_left -= 1
                if retries_left == 0:
                    self._ctx.destroy(linger=0)
                    self._socket.close()
                    raise ConnectionError("[client] Unable to reach the server")
                logging.warning("[client] No response from server")
                # Socket is confused. Close and remove it.
                self._socket.setsockopt(zmq.LINGER, 0)
                self._socket.close()
                logging.warning("[client] Reconnecting to server…")
                # Create new connection
                self._socket = self._ctx.socket(zmq.REQ)
                self._socket.connect(f"tcp://{self._host}:{self._port}")
                logging.warning(f"[client] Resending ({msg})")
                await self._socket.send_multipart([rpc_method_name.encode(), self._encode(msg)], zmq.DONTWAIT)

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
