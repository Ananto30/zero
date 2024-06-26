import asyncio
import logging
import sys
from asyncio import Event
from typing import Dict, Optional

import zmq
import zmq.asyncio as zmqasync
import zmq.error as zmqerr

from zero.error import ConnectionException, TimeoutException
from zero.utils import util


class ZeroMQClient:
    def __init__(self, default_timeout):
        self._address = None
        self._default_timeout = default_timeout
        self._context = zmq.Context.instance()

        self.socket = self._context.socket(zmq.DEALER)
        self.socket.setsockopt(zmq.LINGER, 0)  # dont buffer messages
        self.socket.setsockopt(zmq.RCVTIMEO, default_timeout)
        self.socket.setsockopt(zmq.SNDTIMEO, default_timeout)

        self.poller = zmq.Poller()
        self.poller.register(self.socket, zmq.POLLIN)

    def connect(self, address: str) -> None:
        self._address = address
        self.socket.connect(address)
        self._send(util.unique_id().encode() + b"connect" + b"")
        self._recv()
        logging.info("Connected to server at %s", self._address)

    def request(self, message: bytes, timeout: Optional[int] = None) -> bytes:
        _timeout = self._default_timeout if timeout is None else timeout

        def _poll_data():
            # poll is slow, need to find a better way
            if not self._poll(_timeout):
                raise TimeoutException(f"Timeout while sending message at {self._address}")

            rcv_data = self._recv()

            # first 32 bytes as response id
            resp_id = rcv_data[:32].decode()

            # the rest is response data
            resp_data = rcv_data[32:]

            return resp_id, resp_data

        req_id = util.unique_id()
        self._send(req_id.encode() + message)

        resp_id, resp_data = None, None
        # as the client is synchronous, we know that the response will be available any next poll
        # we try to get the response until timeout because a previous call might be timed out
        # and the response is still in the socket,
        # so we poll until we get the response for this call
        while resp_id != req_id:
            resp_id, resp_data = _poll_data()

        return resp_data  # type: ignore

    def close(self) -> None:
        self.socket.close()

    def _send(self, message: bytes) -> None:
        try:
            self.socket.send(message, zmq.NOBLOCK)
        except zmqerr.Again as exc:
            raise ConnectionException(f"Connection error for send at {self._address}") from exc

    def _poll(self, timeout: int) -> bool:
        socks = dict(self.poller.poll(timeout))
        return self.socket in socks

    def _recv(self) -> bytes:
        try:
            return self.socket.recv()
        except zmqerr.Again as exc:
            raise ConnectionException(f"Connection error for recv at {self._address}") from exc


class AsyncZeroMQClient:
    def __init__(self, default_timeout: int = 2000):
        if sys.platform == "win32":
            # windows need special event loop policy to work with zmq
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

        self._address: str = None  # type: ignore
        self._default_timeout = default_timeout
        self._context = zmqasync.Context.instance()

        self.socket: zmqasync.Socket = self._context.socket(zmq.DEALER)
        self.socket.setsockopt(zmq.LINGER, 0)  # dont buffer messages
        self.socket.setsockopt(zmq.RCVTIMEO, default_timeout)
        self.socket.setsockopt(zmq.SNDTIMEO, default_timeout)

        self.poller = zmqasync.Poller()
        self.poller.register(self.socket, zmq.POLLIN)

        self._resp_map: Dict[str, bytes] = {}

        # self.peer1, self.peer2 = zpipe_async(self._context)

    async def connect(self, address: str) -> None:
        self._address = address
        self.socket.connect(address)
        await self._send(util.unique_id().encode() + b"connect" + b"")
        await self._recv()
        logging.info("Connected to server at %s", self._address)

    async def request(self, message: bytes, timeout: Optional[int] = None) -> bytes:
        _timeout = self._default_timeout if timeout is None else timeout
        expire_at = util.current_time_us() + (_timeout * 1000)

        is_data = Event()

        async def _poll_data():
            # async has issue with poller, after 3-4 calls, it returns empty
            # if not await self._poll(_timeout):
            #     raise TimeoutException(f"Timeout while sending message at {self._address}")

            resp = await self._recv()

            # first 32 bytes as response id
            resp_id = resp[:32].decode()

            # the rest is response data
            resp_data = resp[32:]
            self._resp_map[resp_id] = resp_data

            # pipe is a good way to notify the main event loop that there is a response
            # but pipe is actually slower than sleep, because it is a zmq socket
            # yes it uses inproc, but still slower than asyncio.sleep
            # try:
            #     await self.peer1.send(b"")
            # except zmqerr.Again:
            #     # if the pipe is full, just pass
            #     pass

            is_data.set()

        req_id = util.unique_id()
        await self._send(req_id.encode() + message)

        # poll can get response of a different call
        # so we poll until we get the response of this call or timeout
        await _poll_data()

        while req_id not in self._resp_map:
            if util.current_time_us() > expire_at:
                raise TimeoutException(f"Timeout while waiting for response at {self._address}")

            # await asyncio.sleep(1e-6)
            await asyncio.wait_for(is_data.wait(), timeout=_timeout)

            # try:
            #     await self.peer2.recv()
            # except zmqerr.Again:
            #     # if the pipe is empty, just pass
            #     pass

        resp_data = self._resp_map.pop(req_id)

        return resp_data

    def close(self) -> None:
        self.socket.close()
        self._resp_map.clear()

    async def _send(self, message: bytes) -> None:
        try:
            await self.socket.send(message, zmq.NOBLOCK)
        except zmqerr.Again as exc:
            raise ConnectionException(f"Connection error for send at {self._address}") from exc

    async def _poll(self, timeout: int) -> bool:
        socks = dict(await self.poller.poll(timeout))
        return self.socket in socks

    async def _recv(self) -> bytes:
        try:
            return await self.socket.recv()
        except zmqerr.Again as exc:
            raise ConnectionException(f"Connection error for recv at {self._address}") from exc
