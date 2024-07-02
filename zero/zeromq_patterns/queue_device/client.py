import asyncio
import logging
import sys
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
    def __init__(self, default_timeout: int, concurrency: int):
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

        self._resp_futures: Dict[bytes, asyncio.Future] = {}

        self._semaphore = asyncio.BoundedSemaphore(concurrency)

    async def connect(self, address: str) -> None:
        self._address = address
        self.socket.connect(address)
        await self._send(util.unique_id_bytes() + b"connect" + b"")
        await self._recv()
        logging.info("Connected to server at %s", self._address)

    async def request(self, message: bytes, timeout: Optional[int] = None) -> bytes:
        _timeout = timeout or self._default_timeout
        _expire_at = (asyncio.get_event_loop().time() * 1e3) + _timeout

        async def _poll_data():
            while True:
                try:
                    resp = await self._recv()
                    break
                except ConnectionException as exc:
                    # server is busy processing previous requests
                    # so we need to poll again
                    await asyncio.sleep(0.01)
                    if asyncio.get_event_loop().time() * 1e3 > _expire_at:
                        raise TimeoutException(
                            f"Timeout while sending message at {self._address}"
                        ) from exc

            # first 16 bytes as response id
            resp_id = resp[:16]

            # the rest is response data
            resp_data = resp[16:]

            future = self._resp_futures.pop(resp_id, None)
            if future and not future.done():
                future.set_result(resp_data)

        req_id = util.unique_id_bytes()
        future = self._resp_futures[req_id] = asyncio.Future()

        async with self._semaphore:
            await self._send(req_id + message)

            _timeout_in_sec = _timeout / 1e3
            try:
                await asyncio.wait_for(_poll_data(), _timeout_in_sec)
                resp_data = await asyncio.wait_for(future, _timeout_in_sec)
            except asyncio.TimeoutError as exc:
                self._resp_futures.pop(req_id, None)
                raise TimeoutException(
                    f"Timeout while waiting for response at {self._address}"
                ) from exc

            return resp_data

    def close(self) -> None:
        self.socket.close()
        self._resp_futures.clear()

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
