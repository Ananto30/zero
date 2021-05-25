import msgpack
import zmq
import zmq.asyncio

from .common import check_allowed_types


class ZeroPublisher:
    def __init__(self, host: str, port: int, use_async: bool = True):
        self.__host = host
        self.__port = port
        self.__socket = None
        if use_async:
            self._init_async_socket()
        else:
            self._init_sync_socket()

    def _init_sync_socket(self):
        ctx = zmq.Context()
        self.__socket: zmq.Socket = ctx.socket(zmq.PUB)
        self._set_socket_opt()
        self.__socket.connect(f"tcp://{self.__host}:{self.__port}")

    def _init_async_socket(self):
        ctx = zmq.asyncio.Context()
        self.__socket: zmq.Socket = ctx.socket(zmq.PUB)
        self._set_socket_opt()
        self.__socket.connect(f"tcp://{self.__host}:{self.__port}")

    def _set_socket_opt(self):
        # self.__socket.setsockopt(zmq.RCVTIMEO, 2000)
        # self.__socket.setsockopt(zmq.LINGER, 0)
        pass

    def publish(self, topic, msg):
        check_allowed_types(msg)
        self.__socket.send_multipart([topic.encode(), msgpack.packb(msg)])

    async def publish_async(self, topic, msg):
        check_allowed_types(msg)
        await self.__socket.send_multipart([topic.encode(), msgpack.packb(msg)])
