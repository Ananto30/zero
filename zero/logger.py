import logging
from multiprocessing import Process

import zmq.asyncio

from zero.common import SingletonMeta


class Logger(metaclass=SingletonMeta):
    def __init__(self):
        self._init_push_logger()

    def _init_push_logger(self):
        ctx = zmq.asyncio.Context()
        self.log_pusher = ctx.socket(zmq.PUSH)
        self.log_pusher.connect("tcp://127.0.0.1:12345")

    def log(self, msg):
        self.log_pusher.send_string(msg)


class AsyncLogger:
    @staticmethod
    def log_poller():
        ctx = zmq.Context()
        log_listener = ctx.socket(zmq.PULL)
        log_listener.bind("tcp://127.0.0.1:12345")
        while True:
            log = log_listener.recv_string()
            logging.info(log)

    @staticmethod
    def start():
        Process(target=AsyncLogger.log_poller, args=()).start()
