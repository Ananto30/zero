import asyncio
import logging
import sys
import time
from typing import Dict, Optional

import zmq
import zmq.asyncio as zmqasync
import zmq.error as zmqerr

from zero.error import ConnectionException, TimeoutException
from zero.utils import util


class ZeroMQClient:
    def __init__(self, default_timeout: int):
        self._address = ""
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
        self._send(util.unique_id_bytes() + b"connect" + b"")
        self._recv()
        logging.info("Connected to server at %s", self._address)

    def request(self, message: bytes, timeout: Optional[int] = None) -> bytes:
        _timeout = timeout or self._default_timeout
        _expire_at = int(time.time() * 1e3) + _timeout

        def _poll_data():
            # poll is slow, need to find a better way
            if not self._poll(_timeout):
                raise TimeoutException(
                    f"Timeout while sending message at {self._address}"
                )

            rcv_data = self._recv()

            # first 16 bytes as response id
            resp_id = rcv_data[:16]

            # the rest is response data
            resp_data = rcv_data[16:]

            return resp_id, resp_data

        req_id = util.unique_id_bytes()
        self._send(req_id + message)

        resp_id, resp_data = None, None
        # as the client is synchronous, we know that the response will be available any next poll
        # we try to get the response until timeout because a previous call might be timed out
        # and the response is still in the socket,
        # so we poll until we get the response for this call
        while resp_id != req_id:
            _timeout = _expire_at - int(time.time() * 1e3)
            resp_id, resp_data = _poll_data()

        return resp_data  # type: ignore

    def close(self) -> None:
        self.socket.close()

    def _send(self, message: bytes) -> None:
        try:
            self.socket.send(message, zmq.NOBLOCK)
        except zmqerr.Again as exc:
            raise ConnectionException(
                f"Connection error for send at {self._address}"
            ) from exc

    def _poll(self, timeout: int) -> bool:
        socks = dict(self.poller.poll(timeout))
        return self.socket in socks

    def _recv(self) -> bytes:
        try:
            return self.socket.recv()
        except zmqerr.Again as exc:
            raise ConnectionException(
                f"Connection error for recv at {self._address}"
            ) from exc


class AsyncZeroMQClient:
    def __init__(self, default_timeout: int):
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

        self._resp_events: Dict[bytes, asyncio.Event] = {}
        self._resp_data: Dict[bytes, bytes] = {}
        self._recv_task: Optional[asyncio.Task] = None
        self._closed = False

    async def connect(self, address: str) -> None:
        self._address = address
        self.socket.connect(address)
        await self._send(util.unique_id_bytes() + b"connect" + b"")
        await self._recv()
        self._recv_task = asyncio.create_task(self._recv_loop())
        logging.info("Connected to server at %s", self._address)

    async def _recv_loop(self) -> None:
        while not self._closed:
            resp = await self._recv()
            resp_id, resp_data = resp[:16], resp[16:]
            event = self._resp_events.get(resp_id)
            if event:
                self._resp_data[resp_id] = resp_data
                event.set()

    async def request(self, message: bytes, timeout: Optional[int] = None) -> bytes:
        req_id = util.unique_id_bytes()
        self._resp_events[req_id] = asyncio.Event()
        await self._send(req_id + message)
        try:
            await asyncio.wait_for(
                self._resp_events[req_id].wait(),
                (timeout or self._default_timeout) / 1000,
            )
            return self._resp_data.pop(req_id, b"")
        except asyncio.TimeoutError as exc:
            self._resp_events.pop(req_id, None)
            self._resp_data.pop(req_id, None)
            raise TimeoutException(
                f"Timeout while waiting for response at {self._address}"
            ) from exc

    def close(self) -> None:
        self._closed = True
        if self._recv_task:
            self._recv_task.cancel()
        self.socket.close()
        self._resp_events.clear()
        self._resp_data.clear()

    async def _send(self, message: bytes) -> None:
        try:
            await self.socket.send(message, zmq.NOBLOCK)
        except zmqerr.Again as exc:
            raise ConnectionException(
                f"Connection error for send at {self._address}"
            ) from exc

    async def _recv(self) -> bytes:
        try:
            return await self.socket.recv()
        except zmqerr.Again as exc:
            raise ConnectionException(
                f"Connection error for recv at {self._address}"
            ) from exc
