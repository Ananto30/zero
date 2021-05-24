import logging
import sys
from functools import partial
from multiprocessing import cpu_count
from multiprocessing.pool import Pool

import zmq
import zmq.asyncio

from .worker import Worker

logging.basicConfig(format='%(asctime)s | %(threadName)s | %(process)d | %(module)s : %(message)s', datefmt='%d-%b-%y %H:%M:%S', level=logging.INFO)


class Zero:
    def __init__(self, port=5559):
        self.__rpc_router = {}
        self.__port = port

    def register_rpc(self, rpc_name, func):
        if func.__name__ != rpc_name:
            raise Exception(f"rpc should match function name; `{func.__name__}` doesn't match rpc `{rpc_name}`")
        self.__rpc_router[rpc_name] = func

    def run(self):
        cores = cpu_count()
        pool = Pool(cores)
        try:
            spawn_worker = partial(Worker.spawn_worker, self.__rpc_router)
            pool.map_async(spawn_worker, list(range(1, cores + 1)))
            self._create_zmq_device()
        except KeyboardInterrupt:
            print("Caught KeyboardInterrupt, terminating workers")
            pool.terminate()
        else:
            print("Normal termination")
            pool.close()
        pool.join()

    def _create_zmq_device(self):
        try:
            ctx = zmq.Context()
            gateway = ctx.socket(zmq.ROUTER)  # or XREP
            gateway.bind(f"tcp://*:{self.__port}")
            logging.info(f"Starting server at {self.__port}")
            backend = ctx.socket(zmq.DEALER)  # or XREQ

            if sys.platform == "posix":
                backend.bind("ipc://backendworker")
            else:
                backend.bind("tcp://127.0.0.1:6666")

            # This is the main magic, device works like a queue maintainer
            # Device can be started separately, but we are using as our internal load balancer
            # As python is single process, we are using multiprocessing library to make several process of the same app
            # And to communicate with all the process we are using this device
            # zmq.device(zmq.QUEUE, gateway, backend)
            zmq.proxy(gateway, backend)

        except Exception as e:
            logging.error(e)
            logging.error("bringing down zmq device")
        finally:
            pass
            gateway.close()
            backend.close()
            ctx.term()
