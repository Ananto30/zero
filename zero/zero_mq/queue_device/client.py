import asyncio
import os

import zmq
import zmq.asyncio


class ZeroMQClient:
    def __init__(self, default_timeout):
        self.context = zmq.Context.instance()

        self.socket: zmq.Socket = self.context.socket(zmq.DEALER)
        self.socket.setsockopt(zmq.LINGER, 0)  # dont buffer messages
        self.socket.setsockopt(zmq.RCVTIMEO, default_timeout)
        self.socket.setsockopt(zmq.SNDTIMEO, default_timeout)

        self.poller = zmq.Poller()
        self.poller.register(self.socket, zmq.POLLIN)

    def connect(self, address: str) -> None:
        self.socket.connect(address)

    def close(self) -> None:
        self.socket.close()
        self.context.term()

    def send(self, message: bytes) -> None:
        self.socket.send(message, zmq.DONTWAIT)

    def poll(self, timeout: int) -> bool:
        socks = dict(self.poller.poll(timeout))
        return self.socket in socks

    def recv(self) -> bytes:
        return self.socket.recv()


class AsyncZeroMQClient:
    def __init__(self, default_timeout: int = 2000):
        if os.name == "nt":
            # windows need special event loop policy to work with zmq
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

        self.context = zmq.asyncio.Context.instance()

        self.socket: zmq.asyncio.Socket = self.context.socket(zmq.DEALER)
        self.socket.setsockopt(zmq.LINGER, 0)  # dont buffer messages
        self.socket.setsockopt(zmq.RCVTIMEO, default_timeout)
        self.socket.setsockopt(zmq.SNDTIMEO, default_timeout)

        self.poller = zmq.asyncio.Poller()
        self.poller.register(self.socket, zmq.POLLIN)

    def connect(self, address: str) -> None:
        self.socket.connect(address)

    def close(self) -> None:
        self.socket.close()
        self.context.term()

    async def send(self, message: bytes) -> None:
        await self.socket.send(message, zmq.DONTWAIT)

    async def poll(self, timeout: int) -> bool:
        socks = dict(await self.poller.poll(timeout))
        return self.socket in socks

    async def recv(self) -> bytes:
        return await self.socket.recv()
