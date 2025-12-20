import logging
import os
import signal
import socket
import sys
from functools import partial
from multiprocessing.pool import Pool, ThreadPool
from typing import Callable, Dict, Optional, Tuple

from zero.encoder import Encoder
from zero.utils import util

from .worker import _TCPWorker


class TCPServer:
    def __init__(
        self,
        address: str,
        rpc_router: Dict[str, Tuple[Callable, bool]],
        rpc_input_type_map: Dict[str, Optional[type]],
        rpc_return_type_map: Dict[str, Optional[type]],
        encoder: Encoder,
        use_threads: bool,
    ):
        if sys.platform == "win32":
            raise RuntimeError("TCPServer is not supported on Windows")

        self._address = address
        self._rpc_router = rpc_router
        self._rpc_input_type_map = rpc_input_type_map
        self._rpc_return_type_map = rpc_return_type_map
        self._encoder = encoder
        self._use_threads = use_threads
        self._pool: Optional[Pool] = None

        # Parse address (handle tcp://host:port or host:port)
        addr = address
        if addr.startswith("tcp://"):
            addr = addr[6:]
        host, port_str = addr.rsplit(":", 1)
        self._host = host
        self._port = int(port_str)

    def start(self, workers: int = os.cpu_count() or 1) -> None:
        """
        Start the TCP server with multiple worker instances.

        Each worker runs in its own process/thread and listens on the same port
        using SO_REUSEPORT for efficient load balancing.
        """
        # Check if port is already in use
        if not self._is_port_available():
            logging.error("Port %d is already in use by another process", self._port)
            sys.exit(1)

        logging.info(
            "Starting TCP server at %s with %d workers", self._address, workers
        )

        spawn_worker = partial(
            _TCPWorker.spawn_worker,
            self._address,
            self._rpc_router,
            self._rpc_input_type_map,
            self._rpc_return_type_map,
            self._encoder,
        )

        self._start_workers(workers, spawn_worker)

    def _is_port_available(self) -> bool:
        try:
            # Parse address if needed
            addr = self._address
            if addr.startswith("tcp://"):
                addr = addr[6:]
            host, port_str = addr.rsplit(":", 1)
            port = int(port_str)

            # Try to bind to the port
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            result = sock.connect_ex((host, port))
            sock.close()

            # If connect fails (returns non-zero), port is available
            return result != 0
        except Exception as e:
            logging.error("Error checking port availability: %s", e, stack_info=True)
            return False

    def _start_workers(self, workers: int, spawn_worker: Callable[[int], None]) -> None:
        if self._use_threads:
            self._pool = ThreadPool(workers)
        else:
            self._pool = Pool(workers)

        worker_ids = list(range(1, workers + 1))
        self._pool.map_async(spawn_worker, worker_ids)

        # Register signal handler for graceful shutdown
        util.register_signal_term(self._sig_handler)

        # Blocking - keeps server running until signal
        # signal.pause() will be interrupted by signal handlers
        while True:
            signal.pause()

    def _sig_handler(self, signum, frame):  # pylint: disable=unused-argument
        logging.warning("Signal %d received, stopping server", signum)
        self.stop()

    def stop(self) -> None:
        logging.warning("Terminating TCP server at %s", self._address)
        if self._pool is not None:
            self._terminate_pool()
        sys.exit(0)

    @util.log_error
    def _terminate_pool(self) -> None:
        if self._pool is not None:
            self._pool.terminate()
            self._pool.close()
            # Note: Do NOT call join() after terminate() as it blocks indefinitely
