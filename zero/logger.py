import logging
import os
import sys

import zmq
import zmq.asyncio


class _AsyncLogger:  # pragma: no cover
    """
    *We don't have any support for async logger now.*

    The idea is to have a push pull based logger to reduce io time in main process.
    Logger will serve the methods like info, warn, error, exception
        and push to the desired tcp or ipc.

    The problem is, as the server runs in several processes,
        the logger makes each instance in each process.
    If we run two servers, we cannot connect to the same ipc or tcp.
    So our logger's tcp or ipc should be dynamic.
    But as we got several instances of the logger,
    we cannot centralize a place from where logger can get the tcp or ipc.
    The end user have to provide the tcp or ipc themselves.
    """

    port = 12345
    ipc = "zerologger"

    def __init__(self):
        # pass
        self.init_push_logger()

    def init_push_logger(self):
        ctx = zmq.asyncio.Context()
        self.log_pusher = ctx.socket(zmq.PUSH)
        if os.name == "posix":
            self.log_pusher.connect(f"ipc://{_AsyncLogger.ipc}")
        else:
            self.log_pusher.connect(f"tcp://127.0.0.1:{_AsyncLogger.port}")

    def log(self, msg):
        self.log_pusher.send_string(str(msg))

    @classmethod
    def start_log_poller(cls, ipc, port):
        _AsyncLogger.port = port
        _AsyncLogger.ipc = ipc

        ctx = zmq.Context()
        log_listener = ctx.socket(zmq.PULL)

        if os.name == "posix":
            log_listener.bind(f"ipc://{_AsyncLogger.ipc}")
            logging.info("Async logger starting at ipc://%s", _AsyncLogger.ipc)
        else:
            log_listener.bind(f"tcp://127.0.0.1:{_AsyncLogger.port}")
            logging.info("Async logger starting at tcp://127.0.0.1:%s", _AsyncLogger.port)
        try:
            while True:
                log = log_listener.recv_string()
                logging.info(log)
        except KeyboardInterrupt:
            print("Caught KeyboardInterrupt, terminating async logger")
        except Exception as exc:  # pylint: disable=broad-except
            print(exc)
        finally:
            log_listener.close()
            sys.exit()
