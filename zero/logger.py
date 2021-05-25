import logging

import zmq.asyncio


class AsyncLogger:

    def __init__(self):
        self._init_push_logger()

    def _init_push_logger(self):
        ctx = zmq.asyncio.Context()
        self.log_pusher = ctx.socket(zmq.PUSH)
        self.log_pusher.connect("tcp://127.0.0.1:12345")

    def log(self, msg):
        self.log_pusher.send_string(str(msg))

    @classmethod
    def start_log_poller(cls):
        ctx = zmq.Context()
        log_listener = ctx.socket(zmq.PULL)
        log_listener.bind("tcp://127.0.0.1:12345")
        logging.info(f"Async logger starting at tcp://127.0.0.1:12345")
        while True:
            log = log_listener.recv_string()
            logging.info(log)
