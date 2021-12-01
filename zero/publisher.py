from typing import Optional

import msgpack
import zmq
import zmq.asyncio

from zero.type_util import verify_allowed_type, verify_topic


class _BasePublisher:
    def __init__(self, host: str, port: int):
        self._host = host
        self._port = port
        self._socket: Optional[zmq.Socket] = None

    def _set_socket_opt(self):
        # self._socket.setsockopt(zmq.RCVTIMEO, 2000)
        self._socket.setsockopt(zmq.LINGER, 0)


class ZeroPublisher(_BasePublisher):
    def __init__(self, host: str, port: int):
        super().__init__(host, port)
        self._init_sync_socket()

    def _init_sync_socket(self):
        ctx = zmq.Context()
        self._socket = ctx.socket(zmq.PUB)
        self._set_socket_opt()
        self._socket.bind(f"tcp://*:{self._port}")

    def publish(self, topic, msg):
        verify_topic(topic)
        verify_allowed_type(msg)
        self._socket.send_multipart([topic.encode(), msgpack.packb(msg)])


class AsyncZeroPublisher(_BasePublisher):
    def __init__(self, host: str, port: int):
        super().__init__(host, port)
        self._init_async_socket()

    def _init_async_socket(self):
        ctx = zmq.asyncio.Context()
        self._socket = ctx.socket(zmq.PUB)
        self._set_socket_opt()
        self._socket.bind(f"tcp://{self._host}:{self._port}")

    async def publish(self, topic: str, msg):
        verify_topic(topic)
        verify_allowed_type(msg)
        await self._socket.send_multipart([topic.encode(), msgpack.packb(msg)])
