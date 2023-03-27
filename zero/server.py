import asyncio
import inspect
import logging
import os
import signal
import sys
import time
from functools import partial
from multiprocessing.pool import Pool
from typing import Callable, Dict, Optional

from .codegen import CodeGen
from .encoder import Encoder, get_encoder
from .error import ZeroException
from .type_util import (
    get_function_input_class,
    get_function_return_class,
    verify_function_args,
    verify_function_input_type,
    verify_function_return,
)
from .util import get_next_available_port, register_signal_term, unique_id
from .zero_mq import get_broker, get_worker

# import uvloop


logging.basicConfig(
    format="%(asctime)s  %(levelname)s  %(process)d  %(module)s > %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
    level=logging.INFO,
)

RESERVED_FUNCTIONS = ["get_rpc_contract", "connect"]
ZEROMQ_PATTERN = "queue_device"
ENCODER = "msgpack"


class ZeroServer:
    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 5559,
        encoder: Optional[Encoder] = None,
    ):
        """
        ZeroServer registers rpc methods that are called from a ZeroClient.

        By default ZeroServer uses all of the cores for best performance possible.
        A zmq queue device load balances the requests and runs on the main thread.

        Ensure to run the server inside
        `if __name__ == "__main__":`
        As the server runs on multiple processes.

        Parameters
        ----------
        host: str
            Host of the ZeroServer.
        port: int
            Port of the ZeroServer.
        encoder: Optional[Encoder]
            Encoder to encode/decode messages from/to client.
            Default is msgpack.
            If any other encoder is used, the client should use the same encoder.
            Implement your own encoder by inheriting from `zero.encoder.Encoder`.
        """
        self._port = port
        self._host = host
        self._address = f"tcp://{self._host}:{self._port}"

        # to encode/decode messages from/to client
        self._encoder = encoder or get_encoder(ENCODER)

        # Stores rpc functions
        self._rpc_router: Dict[str, Callable] = {}

        # Stores rpc functions `msg` types
        self._rpc_input_type_map: Dict[str, Optional[type]] = {}
        self._rpc_return_type_map: Dict[str, Optional[type]] = {}

    def register_rpc(self, func: Callable):
        """
        Register the rpc methods available for clients.
        Make sure they return something.
        If the methods don't return anything, it will get timeout in client.

        Parameters
        ----------
        func: typing.Callable
            RPC function.
        """
        self._verify_function_name(func)

        verify_function_args(func)
        verify_function_input_type(func)
        verify_function_return(func)

        self._rpc_input_type_map[func.__name__] = get_function_input_class(func)
        self._rpc_return_type_map[func.__name__] = get_function_return_class(func)

        self._rpc_router[func.__name__] = func

        return func

    def _verify_function_name(self, func):
        if not isinstance(func, Callable):
            raise ZeroException(f"register function; not {type(func)}")
        if func.__name__ in self._rpc_router:
            raise ZeroException(f"cannot have two RPC function same name: `{func.__name__}`")
        if func.__name__ in RESERVED_FUNCTIONS:
            raise ZeroException(
                f"{func.__name__} is a reserved function; cannot have `{func.__name__}` as a RPC function"
            )

    def run(self, cores: int = os.cpu_count() or 1):
        """
        Run the ZeroServer. This is a blocking operation.
        By default it uses all the cores available.

        It starts a zmq queue device on the main process and spawns workers on the background.
        It uses a pool of processes to spawn workers. Each worker is a zmq router.
        A device is used to load balance the requests.

        Parameters
        ----------
        cores: int
            Number of cores to use for the server.
        """
        broker = get_broker(ZEROMQ_PATTERN)

        try:
            # for device-worker communication
            self._device_comm_channel = self._get_comm_channel()

            spawn_worker = partial(
                _Worker.spawn_worker,
                self._rpc_router,
                self._device_comm_channel,
                self._encoder,
                self._rpc_input_type_map,
                self._rpc_return_type_map,
            )

            self._pool = Pool(cores)
            self._pool.map_async(spawn_worker, list(range(1, cores + 1)))

            # process termination signals
            register_signal_term(self._sig_handler)

            # blocking
            broker.listen(self._address, self._device_comm_channel)

            # TODO: by default we start the device with processes, but we need support to run only router
            # asyncio.run(self._start_router())

        except KeyboardInterrupt:
            logging.error("Caught KeyboardInterrupt, terminating workers")
        except Exception as e:
            logging.exception(e)
        finally:
            broker.close()
            self._terminate_server()

    def _get_comm_channel(self) -> str:
        if os.name == "posix":
            ipc_id = unique_id()
            self._device_ipc = f"{ipc_id}.ipc"
            return f"ipc://{ipc_id}.ipc"
        
        # device port is used for non-posix env
        return f"tcp://127.0.0.1:{get_next_available_port(6666)}"

    def _sig_handler(self, signum, frame):
        logging.warn(f"{signal.Signals(signum).name} signal called")
        self._terminate_server()

    def _terminate_server(self):
        logging.warn(f"Terminating server at {self._port}")
        self._pool.terminate()
        self._pool.join()
        self._pool.close()
        try:
            os.remove(self._device_ipc)
        except Exception:
            pass
        sys.exit(1)


class _Worker:
    @classmethod
    def spawn_worker(
        cls,
        rpc_router: dict,
        device_comm_channel: str,
        encoder: Encoder,
        rpc_input_type_map: dict,
        rpc_return_type_map: dict,
        worker_id: int,
    ):
        # give some time for the broker to start
        time.sleep(0.2)

        worker = _Worker(
            rpc_router,
            device_comm_channel,
            encoder,
            rpc_input_type_map,
            rpc_return_type_map,
        )
        # loop = asyncio.get_event_loop()
        # loop.run_until_complete(worker.create_worker(worker_id))
        # asyncio.run(worker.start_async_dealer_worker(worker_id))
        worker.start_dealer_worker(worker_id)

    def __init__(
        self,
        rpc_router: dict,
        device_comm_channel: str,
        encoder: Encoder,
        rpc_input_type_map: dict,
        rpc_return_type_map: dict,
    ):
        self._rpc_router = rpc_router
        self._device_comm_channel = device_comm_channel
        self._loop = asyncio.new_event_loop()
        # self._loop = uvloop.new_event_loop()
        self._rpc_input_type_map = rpc_input_type_map
        self._rpc_return_type_map = rpc_return_type_map
        self.codegen = CodeGen(
            self._rpc_router,
            self._rpc_input_type_map,
            self._rpc_return_type_map,
        )
        self.encoder = encoder

    def start_dealer_worker(self, worker_id):
        def process_message(data: bytes) -> Optional[bytes]:
            try:
                decoded = self.encoder.decode(data)
                req_id, rpc_method, msg = decoded
                response = self._handle_msg(rpc_method, msg)
                return self.encoder.encode([req_id, response])
            except Exception as e:
                logging.exception(e)
                # TODO what to return
                return None

        worker = get_worker(ZEROMQ_PATTERN, worker_id)
        try:
            worker.listen(self._device_comm_channel, process_message)

        except KeyboardInterrupt:
            logging.info("shutting down worker")
        except Exception as e:
            logging.exception(e)
        finally:
            logging.info("closing worker")
            worker.close()

    def _handle_msg(self, rpc, msg):
        if rpc == "get_rpc_contract":
            try:
                return self.codegen.generate_code(msg[0], msg[1])
            except Exception as e:
                logging.exception(e)
                return {"__zerror__failed_to_generate_client_code": str(e)}

        if rpc == "connect":
            return "connected"

        if rpc not in self._rpc_router:
            logging.error(f"method `{rpc}` is not found!")
            return {"__zerror__method_not_found": f"method `{rpc}` is not found!"}

        func = self._rpc_router[rpc]
        try:
            # TODO: is this a bottleneck
            if inspect.iscoroutinefunction(func):
                # this is blocking
                return self._loop.run_until_complete(func() if msg == "" else func(msg))

            return func() if msg == "" else func(msg)

        except Exception as e:
            logging.exception(e)
