import asyncio
import logging
from typing import Awaitable, Callable, Optional

import zmq
import zmq.asyncio


class ZeroMQWorker:
    """Async worker using zmq.asyncio for non-blocking I/O."""

    def __init__(self, worker_id: int):
        self.worker_id = worker_id
        self.context = zmq.asyncio.Context()
        self.socket: zmq.asyncio.Socket = self.context.socket(zmq.DEALER)
        self.socket.setsockopt(zmq.LINGER, 0)  # dont buffer messages
        self.socket.setsockopt(zmq.SNDTIMEO, 2000)

    async def listen(
        self,
        address: str,
        msg_handler: Callable[[bytes, bytes], Awaitable[Optional[bytes]]],
    ) -> None:
        self.socket.connect(address)
        logging.info("Starting worker %d", self.worker_id)

        while True:  # pragma: no cover - hard to test
            try:
                await self._recv_and_process(msg_handler)
            except zmq.error.Again:
                await asyncio.sleep(0.01)

    async def _recv_and_process(
        self, msg_handler: Callable[[bytes, bytes], Awaitable[Optional[bytes]]]
    ):
        # multipart because first frame is ident, set by the broker
        frames = await self.socket.recv_multipart()
        if len(frames) != 2:
            logging.error("invalid message received: %s", frames)
            return

        # ident is set by the broker, because it is a DEALER socket
        # so the broker knows who to send the response to
        ident, data = frames

        # first 16 bytes is request id
        req_id = data[:16]
        data = data[16:]

        # then 80 bytes is function name
        func_name = data[:80].strip()

        # the rest is message
        message = data[80:]

        response = await msg_handler(func_name, message)

        # send is non-blocking with asyncio
        await self.socket.send_multipart(
            [ident, req_id + response if response else b""]
        )

    def close(self) -> None:
        self.socket.close()
        self.context.term()
