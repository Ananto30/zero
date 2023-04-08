import logging

import zmq


class ZeroMQBroker:
    def __init__(self):
        self.context = zmq.Context.instance()

        self.gateway: zmq.Socket = self.context.socket(zmq.ROUTER)
        self.backend: zmq.Socket = self.context.socket(zmq.DEALER)

    def listen(self, address: str, channel: str) -> None:
        self.gateway.bind(f"{address}")
        self.backend.bind(f"{channel}")
        logging.info("Starting server at %s", address)

        zmq.device(zmq.QUEUE, self.gateway, self.backend)

    def close(self) -> None:
        self.gateway.close()
        self.backend.close()
        self.context.term()
