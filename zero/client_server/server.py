import logging
import os
import signal
import sys
from functools import partial
from multiprocessing.pool import Pool
from typing import Callable, Dict, Optional

from zero import config
from zero.client_server.worker import _Worker
from zero.encoder import Encoder, get_encoder
from zero.utils.type import (
    get_function_input_class,
    get_function_return_class,
    verify_function_args,
    verify_function_input_type,
    verify_function_return,
    verify_function_return_type,
)
from zero.utils.util import get_next_available_port, register_signal_term, unique_id
from zero.zero_mq import get_broker

# import uvloop


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
        self._broker = None
        self._device_comm_channel = None
        self._pool = None
        self._device_ipc = None

        self._host = host
        self._port = port
        self._address = f"tcp://{self._host}:{self._port}"

        # to encode/decode messages from/to client
        self._encoder = encoder or get_encoder(config.ENCODER)

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
        verify_function_return_type(func)

        self._rpc_input_type_map[func.__name__] = get_function_input_class(func)
        self._rpc_return_type_map[func.__name__] = get_function_return_class(func)

        self._rpc_router[func.__name__] = func

        return func

    def _verify_function_name(self, func):
        if not isinstance(func, Callable):
            raise ValueError(f"register function; not {type(func)}")
        if func.__name__ in self._rpc_router:
            raise ValueError(
                f"cannot have two RPC function same name: `{func.__name__}`"
            )
        if func.__name__ in config.RESERVED_FUNCTIONS:
            raise ValueError(
                f"{func.__name__} is a reserved function; cannot have `{func.__name__}` "
                "as a RPC function"
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
        self._broker = get_broker(config.ZEROMQ_PATTERN)

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
            self._broker.listen(self._address, self._device_comm_channel)

            # TODO: by default we start the device with processes,
            #  but we need support to run only router
            # asyncio.run(self._start_router())

        except KeyboardInterrupt:
            logging.error("Caught KeyboardInterrupt, terminating workers")
        except Exception as exc:
            logging.exception(exc)
        finally:
            self._terminate_server()

    def _get_comm_channel(self) -> str:
        if os.name == "posix":
            ipc_id = unique_id()
            self._device_ipc = f"{ipc_id}.ipc"
            return f"ipc://{ipc_id}.ipc"

        # device port is used for non-posix env
        return f"tcp://127.0.0.1:{get_next_available_port(6666)}"

    def _sig_handler(self, signum, frame):
        logging.warning("%s signal called", signal.Signals(signum).name)
        self._terminate_server()

    def _terminate_server(self):
        logging.warning("Terminating server at %d", self._port)
        try:
            self._broker.close()
            self._pool.terminate()
            self._pool.join()
            self._pool.close()
            os.remove(self._device_ipc)
        except Exception as exc:
            logging.exception(exc)
        sys.exit(1)
