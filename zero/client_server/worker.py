import asyncio
import inspect
import logging
import time
from typing import Optional

import zero.config as config
from zero.codegen.codegen import CodeGen
from zero.encoder.protocols import Encoder
from zero.zero_mq.factory import get_worker


class _Worker:
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
        self._encoder = encoder
        self._rpc_input_type_map = rpc_input_type_map
        self._rpc_return_type_map = rpc_return_type_map

        self._loop = asyncio.new_event_loop() or asyncio.get_event_loop()

        self.codegen = CodeGen(
            self._rpc_router,
            self._rpc_input_type_map,
            self._rpc_return_type_map,
        )

    def start_dealer_worker(self, worker_id):
        def process_message(data: bytes) -> Optional[bytes]:
            try:
                decoded = self._encoder.decode(data)
                req_id, rpc_method, msg = decoded
                response = self.handle_msg(rpc_method, msg)
                return self._encoder.encode([req_id, response])
            except Exception as e:
                logging.exception(e)
                # TODO what to return
                return None

        worker = get_worker(config.ZEROMQ_PATTERN, worker_id)
        try:
            worker.listen(self._device_comm_channel, process_message)
        except KeyboardInterrupt:
            logging.warning(f"Caught KeyboardInterrupt, terminating worker {worker_id}")
        except Exception as e:
            logging.exception(e)
        finally:
            logging.warning(f"Closing worker {worker_id}")
            worker.close()

    def handle_msg(self, rpc, msg):
        if rpc == "get_rpc_contract":
            return self.generate_rpc_contract(msg)

        if rpc == "connect":
            return "connected"

        if rpc not in self._rpc_router:
            logging.error(f"Function `{rpc}` is not found!")
            return {"__zerror__method_not_found": f"Function `{rpc}` is not found!"}

        func = self._rpc_router[rpc]
        try:
            # TODO: is this a bottleneck
            if inspect.iscoroutinefunction(func):
                # this is blocking
                return self._loop.run_until_complete(func() if msg == "" else func(msg))

            return func() if msg == "" else func(msg)

        except Exception as e:
            logging.exception(e)

    def generate_rpc_contract(self, msg):
        try:
            return self.codegen.generate_code(msg[0], msg[1])
        except Exception as e:
            logging.exception(e)
            return {"__zerror__failed_to_generate_client_code": str(e)}

    @classmethod
    def spawn_worker(
        cls,
        rpc_router: dict,
        device_comm_channel: str,
        encoder: Encoder,
        rpc_input_type_map: dict,
        rpc_return_type_map: dict,
        worker_id: int,
    ) -> None:
        """
        Spawn a worker process.

        A class method is used because the worker process is spawned using multiprocessing.Process.
        The class method is used to avoid pickling the class instance (which can lead to errors).
        """
        # give some time for the broker to start
        time.sleep(0.2)

        worker = _Worker(
            rpc_router,
            device_comm_channel,
            encoder,
            rpc_input_type_map,
            rpc_return_type_map,
        )
        worker.start_dealer_worker(worker_id)