import logging
import os
import signal
import sys
from functools import partial
from multiprocessing.pool import Pool
from typing import Callable, Dict, Optional

import zmq.utils.win32

from zero import config
from zero.encoder import Encoder, get_encoder
from zero.utils import type_util, util
from zero.zero_mq import ZeroMQBroker, get_broker

from .worker import _Worker

# import uvloop


class ZeroServer:
    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 5559,
        encoder: Optional[Encoder] = None,
    ):
        """
        ZeroServer registers and exposes rpc functions that can be called from a ZeroClient.

        By default ZeroServer uses all of the cores for best performance possible.
        A "zmq proxy" load balances the requests and runs on the main thread.

        Parameters
        ----------
        host: str
            Host of the ZeroServer.
        port: int
            Port of the ZeroServer.
        encoder: Optional[Encoder]
            Encoder to encode/decode messages from/to client.
            Default is msgspec.
            If any other encoder is used, the client should use the same encoder.
            Implement custom encoder by inheriting from `zero.encoder.Encoder`.
        """
        self._broker: ZeroMQBroker = None  # type: ignore
        self._device_comm_channel: str = None  # type: ignore
        self._pool: Pool = None  # type: ignore
        self._device_ipc: str = None  # type: ignore

        self._host = host
        self._port = port
        self._address = f"tcp://{self._host}:{self._port}"

        # to encode/decode messages from/to client
        self._encoder = encoder or get_encoder(config.ENCODER)

        # Stores rpc functions against their names
        self._rpc_router: Dict[str, Callable] = {}

        # Stores rpc functions `msg` types
        self._rpc_input_type_map: Dict[str, Optional[type]] = {}
        self._rpc_return_type_map: Dict[str, Optional[type]] = {}

    def register_rpc(self, func: Callable):
        """
        Register a function available for clients.
        Function should have a single argument.
        Argument and return should have a type hint.

        If the function got exception, client will get None as return value.

        Parameters
        ----------
        func: Callable
            RPC function.
        """
        self._verify_function_name(func)
        type_util.verify_function_args(func)
        type_util.verify_function_input_type(func)
        type_util.verify_function_return(func)
        type_util.verify_function_return_type(func)

        self._rpc_input_type_map[func.__name__] = type_util.get_function_input_class(
            func
        )
        self._rpc_return_type_map[func.__name__] = type_util.get_function_return_class(
            func
        )

        self._rpc_router[func.__name__] = func
        return func

    def run(self, workers: int = os.cpu_count() or 1):
        """
        Run the ZeroServer. This is a blocking operation.
        By default it uses all the cores available.

        Ensure to run the server inside
        `if __name__ == "__main__":`
        As the server runs on multiple processes.

        It starts a zmq proxy on the main process and spawns workers on the background.
        It uses a pool of processes to spawn workers. Each worker is a zmq router.
        A proxy device is used to load balance the requests.

        Parameters
        ----------
        workers: int
            Number of workers to spawn.
            Each worker is a zmq router and runs on a separate process.
        """
        self._broker = get_broker(config.ZEROMQ_PATTERN)

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

        try:
            self._start_server(workers, spawn_worker)
        except KeyboardInterrupt:
            logging.warning("Caught KeyboardInterrupt, terminating server")
        except Exception as exc:  # pylint: disable=broad-except
            logging.exception(exc)
        finally:
            self._terminate_server()

    def _start_server(self, workers: int, spawn_worker: Callable):
        self._pool = Pool(workers)

        # process termination signals
        util.register_signal_term(self._sig_handler)

        # TODO: by default we start the workers with processes,
        # but we need support to run only router, without workers
        self._pool.map_async(spawn_worker, list(range(1, workers + 1)))

        # blocking
        with zmq.utils.win32.allow_interrupt(self._terminate_server):
            self._broker.listen(self._address, self._device_comm_channel)

    def _get_comm_channel(self) -> str:
        if os.name == "posix":
            ipc_id = util.unique_id()
            self._device_ipc = f"{ipc_id}.ipc"
            return f"ipc://{ipc_id}.ipc"

        # device port is used for non-posix env
        return f"tcp://127.0.0.1:{util.get_next_available_port(6666)}"

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

    def _sig_handler(self, signum, frame):  # pylint: disable=unused-argument
        logging.warning("%s signal called", signal.Signals(signum).name)
        self._terminate_server()

    def _terminate_server(self):
        logging.warning("Terminating server at %d", self._port)
        if self._broker is not None:
            self._broker.close()
        self._terminate_pool()
        self._remove_ipc()
        sys.exit(0)

    @util.log_error
    def _remove_ipc(self):
        if (
            os.name == "posix"
            and self._device_ipc is not None
            and os.path.exists(self._device_ipc)
        ):
            os.remove(self._device_ipc)

    @util.log_error
    def _terminate_pool(self):
        self._pool.terminate()
        self._pool.close()
        self._pool.join()
