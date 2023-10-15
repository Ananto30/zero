import logging
from typing import Awaitable, Callable, List, Optional

# import zmq.green as zmq
import zmq.asyncio


class ZeroMQWorker:
    def __init__(self, worker_id: int):
        self.worker_id = worker_id
        self.context = zmq.asyncio.Context.instance()

        self.socket: zmq.asyncio.Socket = self.context.socket(zmq.DEALER)
        self.socket.setsockopt(zmq.LINGER, 0)  # dont buffer messages
        # self.socket.setsockopt(zmq.RCVTIMEO, 2000)
        self.socket.setsockopt(zmq.SNDTIMEO, 2000)

    async def listen(
        self, address: str, msg_handler: Callable[[bytes], Awaitable[Optional[bytes]]]
    ) -> None:
        self.socket.connect(address)
        logging.info("Starting worker %d", self.worker_id)

        while True:
            try:
                await self._recv_and_process(msg_handler)
            except zmq.error.Again:
                continue

    async def _recv_and_process(
        self, msg_handler: Callable[[bytes], Awaitable[Optional[bytes]]]
    ):
        frames = await self.socket.recv_multipart()
        if len(frames) != 2:
            logging.error("invalid message received: %s", frames)
            return

        ident, message = frames
        response = await msg_handler(message)
        await self.socket.send_multipart([ident, response], zmq.NOBLOCK, copy=False)

    def close(self) -> None:
        self.socket.close()
        self.context.term()
