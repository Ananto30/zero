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

    def send(self, message: bytes) -> None:
        try:
            self.socket.send(message, zmq.DONTWAIT)
        except zmq.error.Again as exc:
            raise ConnectionException(
                f"Connection error for send at {self._address}"
            ) from exc

    def poll(self, timeout: int) -> bool:
        socks = dict(self.poller.poll(timeout))
        return self.socket in socks

    def recv(self) -> bytes:
        try:
            return self.socket.recv()
        except zmq.error.Again as exc:
            raise ConnectionException(
                f"Connection error for recv at {self._address}"
            ) from exc

    def request(self, message: bytes, timeout: Optional[int] = None) -> bytes:
        try:
            self.send(message)
            if self.poll(timeout or self._default_timeout):
                return self.recv()
            raise TimeoutException(f"Timeout waiting for response from {self._address}")
        except zmq.error.Again as exc:
            raise ConnectionException(
                f"Connection error for request at {self._address}"
            ) from exc


class AsyncZeroMQClient:
    def __init__(self, default_timeout: int = 2000):
        if sys.platform == "win32":
            # windows need special event loop policy to work with zmq
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

        self._default_timeout = default_timeout
        self._context = zmq.asyncio.Context.instance()

        self.socket: zmq.asyncio.Socket = self._context.socket(zmq.DEALER)
        self.socket.setsockopt(zmq.LINGER, 0)  # dont buffer messages
        self.socket.setsockopt(zmq.RCVTIMEO, default_timeout)
        self.socket.setsockopt(zmq.SNDTIMEO, default_timeout)

        self.poller = zmq.asyncio.Poller()
        self.poller.register(self.socket, zmq.POLLIN)

    @property
    def context(self):
        return self._context

    def connect(self, address: str) -> None:
        self._address = address
        self.socket.connect(address)

    def close(self) -> None:
        self.socket.close()

    async def send(self, message: bytes) -> None:
        try:
            await self.socket.send(message, zmq.DONTWAIT)
        except zmq.error.Again as exc:
            raise ConnectionException(
                f"Connection error for send at {self._address}"
            ) from exc

    async def poll(self, timeout: int) -> bool:
        socks = dict(await self.poller.poll(timeout))
        return self.socket in socks

    async def recv(self) -> bytes:
        try:
            return await self.socket.recv()  # type: ignore
        except zmq.error.Again as exc:
            raise ConnectionException(
                f"Connection error for recv at {self._address}"
            ) from exc

    async def request(self, message: bytes, timeout: Optional[int] = None) -> bytes:
        try:
            await self.send(message)
            # TODO async has issue with poller, after 3-4 calls, it returns empty
            # await self.poll(timeout or self._default_timeout)
            return await self.recv()
        except zmq.error.Again as exc:
            raise ConnectionException(
                f"Conection error for request at {self._address}"
            ) from exc
