import asyncio
import inspect
import logging
import os
import signal
import sys
import time
import typing
import uuid
from functools import partial
from multiprocessing.pool import Pool

# import uvloop

import msgpack

import zmq
import zmq.asyncio

from .common import check_allowed_types, get_next_available_port

logging.basicConfig(
    format="%(asctime)s  %(levelname)s  %(process)d  %(module)s > %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
    level=logging.INFO,
)


class ZeroServer:
    def __init__(self, host: str = "127.0.0.1", port: int = 5559, serializer="msgpack"):
        """
        ZeroServer registers rpc methods that are called from a ZeroClient.

        By default ZeroServer uses all of the cores for best performance possible.
        A zmq queue device load balances the requests and runs on the main thread.

        Ensure to run the server inside
        `if __name__ == "__main__":`
        As the server runs on multiple processes.

        @param host:
        Host of the ZeroServer.

        @param port:
        Port of the ZeroServer.

        @param serializer:
        Serializer is used to convert the msg to bytes and vice-versa.
        Only `msgpack` is supported for now.
        """
        self._port = port
        self._host = host
        self._serializer = serializer
        self._rpc_router = {}

        # TODO: quickle is kind of broken for python objects, why? I dont know
        if serializer not in ["msgpack"]:
            raise Exception("serializer not supported")
        # registry for quickle, not used right now
        self._struct_registry = []

    def register_rpc(self, func: typing.Callable):
        """
        Register the rpc methods available for clients.
        Please make sure they return something.
        If the methods don't return anything, use ZeroSubscriber.

        @param func:
        RPC function.
        """
        if not isinstance(func, typing.Callable):
            raise Exception(f"register function; not {type(func)}")
        self._rpc_router[func.__name__] = func
        if typing.get_type_hints(func):
            self._struct_registry.append(typing.get_type_hints(func))

    # quickle is removed as it is kind of broken for python objects, or my mere knowledge
    # def register_msg_types(self, classes: typing.List[quickle.Struct]):
    #     """
    #     Add the list of `quickle.Struct` classes that will be sent in the call.
    #     Only effective for `quickle` serializer.
    #
    #     @param classes: List of Dataclass or python class that extends `quickle.Struct`
    #     """
    #     self._struct_registry = classes

    def run(self):
        try:
            # utilize all the cores
            cores = os.cpu_count()
            # device port is used for non-posix env
            self._device_port = get_next_available_port(6666)
            # ipc is used for posix env
            self._device_ipc = uuid.uuid4().hex[18:]
            self._pool = Pool(cores)
            spawn_worker = partial(
                _Worker.spawn_worker,
                self._rpc_router,
                self._device_ipc,
                self._device_port,
                self._serializer,
                self._struct_registry,
            )
            self._pool.map_async(spawn_worker, list(range(1, cores + 1)))

            signal.signal(signal.SIGTERM, self._sig_handler)
            # TODO: do we need sigkill
            # signal.signal(signal.SIGKILL, self._sig_handler)

            self._start_queue_device()

            # TODO: by default we start the device with processes, but we need support to run only router
            # asyncio.run(self._start_router())

        except KeyboardInterrupt:
            print("Caught KeyboardInterrupt, terminating workers")
        except Exception as e:
            print(e)

    def _sig_handler(self, signum, frame):
        print("Signal handler called with signal", signum)
        self._terminate_server()

    def _terminate_server(self):
        self._pool.terminate()
        self._pool.close()
        self._pool.join()
        sys.exit()

    def _start_queue_device(self):
        try:
            ctx = zmq.Context.instance()
            gateway = ctx.socket(zmq.ROUTER)  # or XREP
            gateway.bind(f"tcp://{self._host}:{self._port}")
            logging.info(f"Starting server at {self._port}")
            backend = ctx.socket(zmq.DEALER)  # or XREQ

            if os.name == "posix":
                backend.bind(f"ipc://{self._device_ipc}")
            else:
                backend.bind(f"tcp://127.0.0.1:{self._device_port}")

            # This is the main magic, device works like a queue maintainer
            # Device can be started separately, but we are using as our internal load balancer
            # As python is single process, we are using multiprocessing library to make several process of the same app
            # And to communicate with all the process we are using this device
            zmq.device(zmq.QUEUE, gateway, backend)
            # zmq.proxy(gateway, backend)

            gateway.close()
            backend.close()
            ctx.term()
        except Exception as e:
            logging.exception(e)
            logging.error("bringing down zmq device")

    async def _start_router(self):
        ctx = zmq.asyncio.Context()
        socket = ctx.socket(zmq.ROUTER)
        socket.bind(f"tcp://127.0.0.1:{self._port}")
        logging.info(f"Starting server at {self._port}")

        while True:
            ident, rpc, msg = await socket.recv_multipart()
            rpc_method = rpc.decode()
            response = await self._handle_msg(rpc_method, msgpack.unpackb(msg))
            try:
                check_allowed_types(response, rpc_method)
            except Exception as e:
                logging.exception(e)
            await socket.send_multipart([ident, msgpack.packb(response)])

    async def _handle_msg(self, rpc, msg):
        if rpc in self._rpc_router:
            try:
                return await self._rpc_router[rpc](msg)
            except Exception as e:
                logging.exception(e)
        else:
            logging.error(f"{rpc} is not found!")


class _Worker:
    @classmethod
    def spawn_worker(
        cls,
        rpc_router: dict,
        ipc: str,
        port: int,
        serializer: str,
        struct_registry: dict,
        worker_id: int,
    ):
        time.sleep(0.2)
        worker = _Worker(rpc_router, ipc, port, serializer, struct_registry)
        # loop = asyncio.get_event_loop()
        # loop.run_until_complete(worker.create_worker(worker_id))
        # asyncio.run(worker.start_async_dealer_worker(worker_id))
        worker.start_dealer_worker(worker_id)

    def __init__(self, rpc_router, ipc, port, serializer, struct_registry):
        self._rpc_router = rpc_router
        self._ipc = ipc
        self._port = port
        self._serializer = serializer
        self._struct_registry = struct_registry
        self._loop = asyncio.get_event_loop()
        # self._loop = uvloop.new_event_loop()
        self._init_serializer()

    def _init_serializer(self):
        # msgpack is the default serializer
        if self._serializer == "msgpack":
            self._encode = msgpack.packb
            self._decode = msgpack.unpackb

    async def start_async_dealer_worker(self, worker_id):
        ctx = zmq.asyncio.Context()
        socket = ctx.socket(zmq.DEALER)

        if os.name == "posix":
            socket.connect(f"ipc://{self._ipc}")
        else:
            socket.connect(f"tcp://127.0.0.1:{self._port}")

        logging.info(f"Starting worker: {worker_id}")

        async def process_message():
            try:
                ident, rpc, msg = await socket.recv_multipart()
                rpc_method = rpc.decode()
                msg = self._decode(msg)
                response = await self._handle_msg_async(rpc_method, msg)
                response = self._encode(response)
                await socket.send_multipart([ident, response], zmq.DONTWAIT)
            except Exception as e:
                logging.exception(e)

        while True:
            await process_message()

    def start_dealer_worker(self, worker_id):
        ctx = zmq.Context()
        socket = ctx.socket(zmq.DEALER)

        if os.name == "posix":
            socket.connect(f"ipc://{self._ipc}")
        else:
            socket.connect(f"tcp://127.0.0.1:{self._port}")

        logging.info(f"Starting worker: {worker_id}")

        def process_message():
            try:
                ident, rpc, msg = socket.recv_multipart()
                rpc_method = rpc.decode()
                msg = self._decode(msg)
                response = self._handle_msg(rpc_method, msg)
                response = self._encode(response)
                socket.send_multipart([ident, response], zmq.DONTWAIT)
            except Exception as e:
                logging.exception(e)

        while True:
            process_message()

    def _handle_msg(self, rpc, msg):
        if rpc in self._rpc_router:
            func = self._rpc_router[rpc]
            try:
                # TODO: is this a bottleneck
                if inspect.iscoroutinefunction(func):
                    return self._loop.run_until_complete(func(msg))
                return func(msg)
            except Exception as e:
                logging.exception(e)
        else:
            logging.error(f"method `{rpc}` is not found!")
            return {"__zerror__method_not_found": f"method `{rpc}` is not found!"}

    async def _handle_msg_async(self, rpc, msg):
        if rpc in self._rpc_router:
            try:
                return await self._rpc_router[rpc](msg)
            except Exception as e:
                logging.exception(e)
        else:
            logging.error(f"method `{rpc}` is not found!")
