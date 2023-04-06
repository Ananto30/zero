import logging
from typing import Callable, Optional

# import zmq.green as zmq
import zmq


class ZeroMQWorker:
    def __init__(self, worker_id: int):
        self.worker_id = worker_id
        self.context = zmq.Context.instance()

        self.socket: zmq.Socket = self.context.socket(zmq.DEALER)
        self.socket.setsockopt(zmq.LINGER, 0)  # dont buffer messages
        self.socket.setsockopt(zmq.RCVTIMEO, 2000)
        self.socket.setsockopt(zmq.SNDTIMEO, 2000)

        self.poller = zmq.Poller()
        self.poller.register(self.socket, zmq.POLLIN)

    def listen(self, address: str, msg_handler: Callable[[bytes], Optional[bytes]]) -> None:
        self.socket.connect(address)
        logging.info(f"Starting worker {self.worker_id}")

        while True:
            socks = dict(self.poller.poll(100))
            if self.socket in socks:
                frames = self.socket.recv_multipart(flags=zmq.NOBLOCK)
                if len(frames) != 2:
                    logging.error(f"Invalid message received: {frames}")
                    continue

                ident, message = frames
                response = msg_handler(message)
                self.socket.send_multipart([ident, response], zmq.NOBLOCK)

    def close(self) -> None:
        self.socket.close()
        self.context.term()
