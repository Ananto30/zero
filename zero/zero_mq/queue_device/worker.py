import logging
from typing import Callable, Optional

import zmq

# import zmq.green as zmq


class ZeroMQWorker:
    def __init__(self, worker_id: int):
        self.worker_id = worker_id
        self.context = zmq.Context()

        self.socket: zmq.Socket = self.context.socket(zmq.DEALER)
        self.socket.setsockopt(zmq.LINGER, 0)  # dont buffer messages
        # self.socket.setsockopt(zmq.RCVTIMEO, 2000)
        self.socket.setsockopt(zmq.SNDTIMEO, 2000)

    def listen(
        self, address: str, msg_handler: Callable[[bytes], Optional[bytes]]
    ) -> None:
        self.socket.connect(address)
        logging.info("Starting worker %d", self.worker_id)

        while True:  # pragma: no cover - hard to test
            try:
                self._recv_and_process(msg_handler)
            except zmq.error.Again:
                continue

    def _recv_and_process(self, msg_handler: Callable[[bytes], Optional[bytes]]):
        frames = self.socket.recv_multipart()
        if len(frames) != 2:
            logging.error("invalid message received: %s", frames)
            return

        ident, message = frames
        response = msg_handler(message)

        # TODO send is slow, need to find a way to make it faster
        self.socket.send_multipart([ident, response], zmq.NOBLOCK)

    def close(self) -> None:
        self.socket.close()
        self.context.term()
