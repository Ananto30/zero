import logging
import typing

import msgpack
import zmq
import zmq.asyncio

from .common import check_allowed_types


class ZeroClient:
    def __init__(self, host: str, port: int, use_async: bool = True):
        self.__host = host
        self.__port = port
        self.__socket = None
        if use_async:
            self._init_async_socket()
        else:
            self._init_socket()

    def _init_socket(self):
        ctx = zmq.Context()
        self.__socket: zmq.Socket = ctx.socket(zmq.DEALER)
        self._set_socket_opt()
        self.__socket.connect(f"tcp://{self.__host}:{self.__port}")

    def _init_async_socket(self):
        ctx = zmq.asyncio.Context()
        self.__socket: zmq.Socket = ctx.socket(zmq.DEALER)
        self._set_socket_opt()
        self.__socket.connect(f"tcp://{self.__host}:{self.__port}")

    def _set_socket_opt(self):
        self.__socket.setsockopt(zmq.RCVTIMEO, 2000)
        self.__socket.setsockopt(zmq.SNDTIMEO, 2000)
        self.__socket.setsockopt(zmq.LINGER, 0)

    def call(self, rpc, msg):
        check_allowed_types(msg)
        try:
            self.__socket.send_multipart([rpc.encode(), msgpack.packb(msg)])
            resp = self.__socket.recv()
            return msgpack.unpackb(resp)
        except Exception as e:
            self.__socket.close()
            self._init_socket()
            logging.error(e)

    async def call_async(self, rpc, msg):
        check_allowed_types(msg)
        try:
            await self.__socket.send_multipart([rpc.encode(), msgpack.packb(msg)])
            resp = await self.__socket.recv()
            return msgpack.unpackb(resp)
        except Exception as e:
            self.__socket.close()
            self._init_async_socket()
            logging.error(e)
