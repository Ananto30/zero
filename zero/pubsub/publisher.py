import msgspec
import zmq
import zmq.asyncio

from zero.utils.type_util import verify_allowed_type


class ZeroPublisher:  # pragma: no cover
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
        self.__socket = ctx.socket(zmq.PUB)
        self._set_socket_opt()
        self.__socket.connect(f"tcp://{self.__host}:{self.__port}")

    def _init_async_socket(self):
        ctx = zmq.asyncio.Context()
        self.__socket = ctx.socket(zmq.PUB)
        self._set_socket_opt()
        self.__socket.connect(f"tcp://{self.__host}:{self.__port}")

    def _set_socket_opt(self):
        # self.__socket.setsockopt(zmq.RCVTIMEO, 2000)
        self.__socket.setsockopt(zmq.LINGER, 0)

    def publish(self, topic, msg):
        verify_allowed_type(msg)
        self.__socket.send_multipart([topic.encode(), msgspec.msgpack.encode(msg)])

    async def publish_async(self, topic, msg):
        verify_allowed_type(msg)
        await self.__socket.send_multipart(
            [topic.encode(), msgspec.msgpack.encode(msg)]
        )
