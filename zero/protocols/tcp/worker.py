import asyncio
import logging
import signal
import sys
from inspect import signature
from typing import Any, Callable, Dict, Optional, Tuple

from zero.encoder import Encoder
from zero.protocols.common_rpc import execute_common_rpc

from .frame_io import read_frame, write_frame


class _TCPWorker:
    """Worker that listens for client connections and processes RPC requests."""

    def __init__(
        self,
        address: str,
        rpc_router: Dict[str, Tuple[Callable, bool]],
        rpc_input_type_map: Dict[str, Optional[type]],
        rpc_return_type_map: Dict[str, Optional[type]],
        encoder: Encoder,
        worker_id: int,
    ):
        if sys.platform == "win32":
            raise RuntimeError("TCPWorker is not supported on Windows")

        self._address = address
        self._rpc_router = rpc_router
        self._rpc_input_type_map = rpc_input_type_map
        self._rpc_return_type_map = rpc_return_type_map
        self._encoder = encoder
        self._worker_id = worker_id

        # Cache function signatures to avoid expensive introspection on every call
        self._func_has_args: Dict[str, bool] = {}
        for fn_name, (func, _) in rpc_router.items():
            sig = signature(func)
            self._func_has_args[fn_name] = len(sig.parameters) > 0

        # Parse address
        addr = address
        if addr.startswith("tcp://"):
            addr = addr[6:]
        host, port_str = addr.rsplit(":", 1)
        self._host = host
        self._port = int(port_str)

        self._server: Optional[asyncio.Server] = None
        self._running = False
        self._main_task: Optional[asyncio.Task] = None

    def start(self) -> None:
        logging.info(
            "Starting TCP worker %d on %s:%d", self._worker_id, self._host, self._port
        )

        try:
            import uvloop

            uvloop.install()
        except Exception as e:
            logging.warning("Failed to install uvloop: %s", e)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self._main_task = loop.create_task(self._main())

        try:
            loop.run_until_complete(self._main_task)

        except asyncio.CancelledError:
            logging.info("Worker %d cancelled", self._worker_id)

        except KeyboardInterrupt:
            logging.info("Worker %d interrupted", self._worker_id)

        finally:
            loop.close()
            sys.exit(0)

    async def _main(self) -> None:
        # Register signal handlers
        loop = asyncio.get_event_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, self._signal_handler)

        # Create listening server with SO_REUSEPORT for multiple workers on same port
        # Note: On Windows, SO_REUSEPORT support is limited; we try with it first,
        # but fall back to without it if needed
        try:
            self._server = await asyncio.start_server(
                self._handle_client,
                self._host,
                self._port,
                reuse_port=True,
            )
        except OSError as e:
            # Fall back to binding without reuse_port on Windows
            logging.warning(
                "Worker %d: Failed to bind with reuse_port, retrying without: %s",
                self._worker_id,
                e,
            )
            self._server = await asyncio.start_server(
                self._handle_client,
                self._host,
                self._port,
                reuse_port=False,
            )

        self._running = True
        addrs = ", ".join(
            str(sock.getsockname()) for sock in self._server.sockets or []
        )
        logging.info("Worker %d listening on %s", self._worker_id, addrs)

        try:
            async with self._server:
                await self._server.serve_forever()

        except asyncio.CancelledError:
            logging.info("Worker %d cancelled", self._worker_id)

        finally:
            self._running = False

    def _signal_handler(self) -> None:
        logging.warning("Worker %d stopping", self._worker_id)
        self._running = False
        if self._server:
            self._server.close()

        if self._main_task and not self._main_task.done():
            self._main_task.cancel()

    async def _handle_client(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        peer = writer.get_extra_info("peername")
        logging.debug("Worker %d: Client connected from %s", self._worker_id, peer)

        try:
            while self._running:
                try:
                    request_id, req_payload, _ = await read_frame(reader)
                    req = self._encoder.decode(req_payload)

                except ConnectionError:
                    logging.debug(
                        "Worker %d: Client %s disconnected", self._worker_id, peer
                    )
                    break

                except asyncio.TimeoutError:
                    logging.warning(
                        "Worker %d: Timeout reading from %s", self._worker_id, peer
                    )
                    break

                resp = await self._process_rpc(req)
                is_error = isinstance(resp, dict) and any(
                    isinstance(key, str) and key.startswith("__zerror__")
                    for key in resp.keys()
                )

                try:
                    await write_frame(writer, resp, self._encoder, request_id, is_error)

                except (BrokenPipeError, ConnectionResetError):
                    logging.debug(
                        "Worker %d: Failed to write to %s", self._worker_id, peer
                    )
                    break

        except asyncio.IncompleteReadError:
            logging.debug(
                "Worker %d: Client %s disconnected unexpectedly", self._worker_id, peer
            )

        except Exception as e:  # pylint: disable=broad-except
            logging.error(
                "Worker %d: Error handling %s: %s",
                self._worker_id,
                peer,
                e,
                exc_info=e,
            )

        finally:
            try:
                writer.close()
                await writer.wait_closed()
            except Exception:  # pylint: disable=broad-except
                pass

    async def _process_rpc(self, req: Dict[str, Any]) -> Any:
        """
        Process an RPC request.

        Parameters
        ----------
        req : Dict[str, Any]
            Request message (should be a dict with 'fn' and 'data' keys)

        Returns
        -------
        Any
            The function result on success, or error dict with '__zerror__*' keys on failure
        """
        try:
            if not isinstance(req, dict):
                return {"__zerror__server_exception": "Request must be a dict"}

            fn_name = req.get("fn")
            data = req.get("data")

            if not fn_name:
                return {"__zerror__server_exception": "Missing function name"}

            if common_rpc := execute_common_rpc(
                fn_name,
                data,
                self._rpc_router,
                self._rpc_input_type_map,
                self._rpc_return_type_map,
            ):
                return common_rpc

            func, is_coro = self._rpc_router[fn_name]

            try:
                if is_coro:
                    result = (
                        await func(data)
                        if self._func_has_args[fn_name]
                        else await func()
                    )
                else:
                    # Run sync function in thread pool to avoid blocking event loop
                    result = (
                        await asyncio.to_thread(func, data)
                        if self._func_has_args[fn_name]
                        else await asyncio.to_thread(func)
                    )

                return result

            except Exception as e:  # pylint: disable=broad-except
                logging.error(
                    "Worker %d: Error calling %s: %s",
                    self._worker_id,
                    fn_name,
                    e,
                    exc_info=e,
                )
                return {"__zerror__server_exception": repr(e)}

        except Exception as e:  # pylint: disable=broad-except
            logging.error(
                "Worker %d: Error processing RPC: %s", self._worker_id, e, exc_info=e
            )
            return {"__zerror__server_exception": repr(e)}

    @classmethod
    def spawn_worker(
        cls,
        address: str,
        rpc_router: Dict[str, Tuple[Callable, bool]],
        rpc_input_type_map: Dict[str, Optional[type]],
        rpc_return_type_map: Dict[str, Optional[type]],
        encoder: Encoder,
        worker_id: int,
    ) -> None:
        """
        Spawn a worker process.

        This is a class method to be used with multiprocessing.Pool.map_async().
        Each worker runs its own asyncio event loop and listens on the same port.
        """
        worker = cls(
            address,
            rpc_router,
            rpc_input_type_map,
            rpc_return_type_map,
            encoder,
            worker_id,
        )
        worker.start()
