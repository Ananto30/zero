import logging
import os
import signal
import sys
from functools import partial
from multiprocessing.pool import Pool
from typing import Callable, Dict, Optional, Tuple

import zmq.utils.win32

from zero import config
from zero.encoder import Encoder
from zero.utils import util
from zero.zeromq_patterns import ZeroMQBroker, get_broker

from .worker import _Worker

# import uvloop


class ZMQServer:
    def __init__(
        self,
        address: str,
        rpc_router: Dict[str, Tuple[Callable, bool]],
        rpc_input_type_map: Dict[str, Optional[type]],
        rpc_return_type_map: Dict[str, Optional[type]],
        encoder: Encoder,
    ):
        self._broker: ZeroMQBroker = None  # type: ignore
        self._device_comm_channel: str = None  # type: ignore
        self._pool: Pool = None  # type: ignore
        self._device_ipc: str = None  # type: ignore

        self._address = address
        self._rpc_router = rpc_router
        self._rpc_input_type_map = rpc_input_type_map
        self._rpc_return_type_map = rpc_return_type_map
        self._encoder = encoder

    def start(self, workers: int = os.cpu_count() or 1):
        """
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

        self._start_server(workers, spawn_worker)

    def _start_server(self, workers: int, spawn_worker: Callable):
        self._pool = Pool(workers)

        # process termination signals
        util.register_signal_term(self._sig_handler)

        # TODO: by default we start the workers with processes,
        # but we need support to run only router, without workers
        self._pool.map_async(spawn_worker, list(range(1, workers + 1)))

        # blocking
        with zmq.utils.win32.allow_interrupt(self.stop):
            self._broker.listen(self._address, self._device_comm_channel)

    def _get_comm_channel(self) -> str:
        if os.name == "posix":
            ipc_id = util.unique_id()
            self._device_ipc = f"{ipc_id}.ipc"
            return f"ipc://{ipc_id}.ipc"

        # device port is used for non-posix env
        return f"tcp://127.0.0.1:{util.get_next_available_port(6666)}"

    def _sig_handler(self, signum, frame):  # pylint: disable=unused-argument
        logging.warning("%s signal called", signal.Signals(signum).name)
        self.stop()

    def stop(self):
        logging.warning("Terminating server at %s", self._address)
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
