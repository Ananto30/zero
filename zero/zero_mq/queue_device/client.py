import asyncio
import sys
from typing import Optional

import zmq
import zmq.asyncio

from zero.error import ConnectionException, TimeoutException


class ZeroMQClient:
    def __init__(self, default_timeout):
        self._default_timeout = default_timeout
        self._context = zmq.Context.instance()

        self.socket: zmq.Socket = self._context.socket(zmq.DEALER)
        self.socket.setsockopt(zmq.LINGER, 0)  # dont buffer messages
        self.socket.setsockopt(zmq.RCVTIMEO, default_timeout)
        self.socket.setsockopt(zmq.SNDTIMEO, default_timeout)

        self.poller = zmq.Poller()
        self.poller.register(self.socket, zmq.POLLIN)

    @property
    def context(self):
        return self._context

    def connect(self, address: str) -> None:
        self._address = address
        self.socket.connect(address)

    def close(self) -> None:
        self.socket.close()
        self._context.term()

    def send(self, message: bytes) -> None:
        self.socket.send(message, zmq.DONTWAIT)

    def poll(self, timeout: int) -> bool:
        socks = dict(self.poller.poll(timeout))
        return self.socket in socks

    def recv(self) -> bytes:
        return self.socket.recv()

    def request(self, message: bytes, timeout: Optional[int] = None) -> bytes:
        try:
            self.send(message)
            if self.poll(timeout or self._default_timeout):
                return self.recv()
            raise TimeoutException(f"Timeout waiting for response from {self._address}")
        except zmq.error.Again:
            raise ConnectionException(f"Cannot connect to server at {self._address}")


class AsyncZeroMQClient:
    def __init__(self, default_timeout: int = 2000):
        if sys.platform == "win32":
            # windows need special event loop policy to work with zmq
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

        self._default_timeout = default_timeout
        self.context = zmq.asyncio.Context.instance()

        self.socket: zmq.asyncio.Socket = self.context.socket(zmq.DEALER)
        self.socket.setsockopt(zmq.LINGER, 0)  # dont buffer messages
        self.socket.setsockopt(zmq.RCVTIMEO, default_timeout)
        self.socket.setsockopt(zmq.SNDTIMEO, default_timeout)

        self.poller = zmq.asyncio.Poller()
        self.poller.register(self.socket, zmq.POLLIN)

    def connect(self, address: str) -> None:
        self._address = address
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
        return await self.socket.recv()  # type: ignore

    async def request(self, message: bytes, timeout: Optional[int] = None) -> bytes:
        try:
            await self.send(message)
            # TODO async has issue with poller, after 3-4 calls, it returns empty
            # await self.poll(timeout or self._default_timeout)
            return await self.recv()
        except zmq.error.Again:
            raise ConnectionException(f"Cannot connect to server at {self._address}")
