import asyncio
import logging
import multiprocessing
from multiprocessing import cpu_count

import msgpack
import zmq
import zmq.asyncio

from zero.common import check_allowed_types

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
        # Generally use the number of cores * 2 - 1
        cores = cpu_count()
        pool = multiprocessing.Pool(cores)
        try:
            pool.map_async(self._spawn_worker, list(range(1, cores)))
            self._create_zmq_device()
        except KeyboardInterrupt:
            print("Caught KeyboardInterrupt, terminating workers")
            pool.terminate()
        else:
            print("Normal termination")
            pool.close()
        pool.join()

    async def _handle_msg(self, rpc, msg):
        if rpc in self.__rpc_router:
            try:
                return await self.__rpc_router[rpc](msg)
            except Exception as e:
                logging.error(e)
        else:
            logging.error(f"{rpc} is not found!")

    def _spawn_worker(self, worker_id):
        asyncio.run(self._create_worker(worker_id))

    async def _create_worker(self, worker_id):
        ctx = zmq.asyncio.Context()
        socket = ctx.socket(zmq.DEALER)
        socket.connect("ipc://backendworker")
        logging.info(f"Starting worker: {worker_id}")
        while True:
            ident, rpc, msg = await socket.recv_multipart()
            # logging.info(f"received rpc call: {rpc.decode()} | {msg}")
            response = await self._handle_msg(rpc.decode(), msgpack.unpackb(msg))
            try:
                check_allowed_types(response)
            except Exception as e:
                logging.error(e)
            # logging.info(f"send rpc response: {response}")
            await socket.send_multipart([ident, msgpack.packb(response)])

    def _create_zmq_device(self):
        try:
            ctx = zmq.Context()
            gateway = ctx.socket(zmq.ROUTER)  # or XREP
            gateway.bind(f"tcp://*:{self.__port}")
            logging.info(f"Starting server at {self.__port}")
            backend = ctx.socket(zmq.DEALER)  # or XREQ
            backend.bind("ipc://backendworker")

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
