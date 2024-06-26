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
        self, address: str, msg_handler: Callable[[bytes, bytes], Optional[bytes]]
    ) -> None:
        self.socket.connect(address)
        logging.info("Starting worker %d", self.worker_id)

        while True:  # pragma: no cover - hard to test
            try:
                self._recv_and_process(msg_handler)
            except zmq.error.Again:
                continue

    def _recv_and_process(self, msg_handler: Callable[[bytes, bytes], Optional[bytes]]):
        # multipart because first frame is ident, set by the broker
        frames = self.socket.recv_multipart()
        if len(frames) != 2:
            logging.error("invalid message received: %s", frames)
            return

        # ident is set by the broker, because it is a DEALER socket
        # so the broker knows who to send the response to
        ident, data = frames

        # first 32 bytes is request id
        req_id = data[:32]

        # then 120 bytes is function name
        func_name = data[32:152].strip()

        # the rest is message
        message = data[152:]

        response = msg_handler(func_name, message)

        # TODO send is slow, need to find a way to make it faster
        self.socket.send_multipart(
            [ident, req_id + response if response else b""], copy=False
        )

    def close(self) -> None:
        self.socket.close()
        self.context.term()
