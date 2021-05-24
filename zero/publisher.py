import msgpack
import zmq
import zmq.asyncio

from .common import check_allowed_types


class ZeroPublisher:
    def __init__(self, host, port, use_async=False):
        self.__host = host
        self.__port = port
        self.__socket = None
        if use_async:
            self._init_async_socket()

    def _init_async_socket(self):
        ctx = zmq.asyncio.Context()
        self.__socket: zmq.Socket = ctx.socket(zmq.PUB)
        self.__socket.setsockopt(zmq.SNDTIMEO, 2000)
        self.__socket.setsockopt(zmq.LINGER, 0)
        self.__socket.connect(f"tcp://{self.__host}:{self.__port}")

    def publish(self, topic, msg):
        check_allowed_types(msg)
        self.__socket.send_multipart([topic.encode(), msgpack.packb(msg)])

    async def publish_async(self, topic, msg):
        check_allowed_types(msg)
        await self.__socket.send_multipart([topic.encode(), msgpack.packb(msg)])
