import asyncio
import logging
import sys
import typing
from functools import partial
from multiprocessing import cpu_count
from multiprocessing.pool import Pool

import msgpack
import zmq
import zmq.asyncio
import zmq.asyncio

from .common import check_allowed_types
from .logger import AsyncLogger

logging.basicConfig(format='%(asctime)s | %(threadName)s | %(process)d | %(module)s : %(message)s', datefmt='%d-%b-%y %H:%M:%S', level=logging.INFO)


class ZeroServer:
    def __init__(self, host: str = "127.0.0.1", port: int = 5559, use_async_logger: bool = True):
        self.__rpc_router = {}
        self.__port = port
        self.__host = host
        self.__use_async_logger = use_async_logger

    def register_rpc(self, func: typing.Callable):
        if not isinstance(func, typing.Callable):
            raise Exception(f"register function not {type(func)}")
        self.__rpc_router[func.__name__] = func

    def run(self):
        cores = cpu_count()
        pool = Pool(cores + 1)
        try:
            spawn_worker = partial(Worker.spawn_worker, self.__rpc_router)
            pool.map_async(spawn_worker, list(range(1, cores + 1)))
            if self.__use_async_logger:
                pool.starmap_async(AsyncLogger.start_log_poller, [()])

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
            gateway.bind(f"tcp://{self.__host}:{self.__port}")
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
            zmq.device(zmq.QUEUE, gateway, backend)
            # zmq.proxy(gateway, backend)

        except Exception as e:
            logging.error(e)
            logging.error("bringing down zmq device")
        finally:
            pass
            gateway.close()
            backend.close()
            ctx.term()


class Worker:

    @classmethod
    def spawn_worker(cls, rpc_router, worker_id):
        worker = Worker(rpc_router)
        asyncio.run(worker.create_worker(worker_id))

    def __init__(self, rpc_router):
        self.__rpc_router = rpc_router

    async def create_worker(self, worker_id):
        ctx = zmq.asyncio.Context()
        socket = ctx.socket(zmq.DEALER)

        if sys.platform == "posix":
            socket.connect("ipc://backendworker")
        else:
            socket.connect("tcp://127.0.0.1:6666")

        logging.info(f"Starting worker: {worker_id}")

        while True:
            ident, rpc, msg = await socket.recv_multipart()
            rpc_method = rpc.decode()
            response = await self._handle_msg(rpc_method, msgpack.unpackb(msg))
            try:
                check_allowed_types(response, rpc_method)
            except Exception as e:
                logging.error(e)
            await socket.send_multipart([ident, msgpack.packb(response)])

    async def _handle_msg(self, rpc, msg):
        if rpc in self.__rpc_router:
            try:
                return await self.__rpc_router[rpc](msg)
            except Exception as e:
                logging.exception(e)
        else:
            logging.error(f"{rpc} is not found!")
