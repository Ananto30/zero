import logging
import os
import sys

import zmq.asyncio

'''
*We don't have any support for async logger now.*

The idea is to have a push pull based logger to reduce io time in main process.
Logger will serve the methods like info, warn, error, exception and push to the desired tcp or ipc.

The problem is, as the server runs in several processes, the logger makes each instance in each process.
If we run two servers, we cannot connect to the same ipc or tcp.
So our logger's tcp or ipc should be dynamic. 
But as we got several instances of the logger, we cannot centralize a place from where logger can get the tcp or ipc.
The end user have to provide the tcp or ipc themselves.
'''


class AsyncLogger:
    port = 12345
    ipc = "zerologger"

    def __init__(self):
        # pass
        self.init_push_logger()

    def init_push_logger(self):
        ctx = zmq.asyncio.Context()
        self.log_pusher = ctx.socket(zmq.PUSH)
        if os.name == "posix":
            self.log_pusher.connect(f"ipc://{AsyncLogger.ipc}")
        else:
            self.log_pusher.connect(f"tcp://127.0.0.1:{AsyncLogger.port}")

    def log(self, msg):
        self.log_pusher.send_string(str(msg))

    @classmethod
    def start_log_poller(cls, ipc, port):
        AsyncLogger.port = port
        AsyncLogger.ipc = ipc

        ctx = zmq.Context()
        log_listener = ctx.socket(zmq.PULL)

        if os.name == "posix":
            log_listener.bind(f"ipc://{AsyncLogger.ipc}")
            logging.info(f"Async logger starting at ipc://{AsyncLogger.ipc}")
        else:
            log_listener.bind(f"tcp://127.0.0.1:{AsyncLogger.port}")
            logging.info(f"Async logger starting at tcp://127.0.0.1:{AsyncLogger.port}")
        try:
            while True:
                log = log_listener.recv_string()
                logging.info(log)
        except KeyboardInterrupt:
            print("Caught KeyboardInterrupt, terminating async logger")
        except Exception as e:
            print(e)
        except:
            print("Unknown error!")
        finally:
            log_listener.close()
            sys.exit()
