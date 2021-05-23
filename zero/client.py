import msgpack
import zmq
import zmq.asyncio

from zero.common import check_allowed_types


class ZeroClient:
    def __init__(self, host, port):
        self.__host = host
        self.__port = port
        self._init_socket()
        self._init_async_socket()

    def _init_socket(self):
        ctx = zmq.Context()
        self.__socket: zmq.Socket = ctx.socket(zmq.DEALER)
        self.__socket.setsockopt(zmq.RCVTIMEO, 10000)
        self.__socket.connect(f"tcp://{self.__host}:{self.__port}")

    def _init_async_socket(self):
        ctx = zmq.asyncio.Context()
        self.__async_socket: zmq.Socket = ctx.socket(zmq.DEALER)
        self.__async_socket.setsockopt(zmq.RCVTIMEO, 10000)
        self.__async_socket.connect(f"tcp://{self.__host}:{self.__port}")

    def call(self, rpc, msg):
        check_allowed_types(msg)
        self.__socket.send_multipart([rpc.encode(), msgpack.packb(msg)])
        resp = self.__socket.recv()
        return msgpack.unpackb(resp)

    async def call_async(self, rpc, msg):
        check_allowed_types(msg)
        await self.__async_socket.send_multipart([rpc.encode(), msgpack.packb(msg)])
        resp = await self.__async_socket.recv()
        return msgpack.unpackb(resp)
