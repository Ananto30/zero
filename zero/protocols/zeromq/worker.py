import asyncio
import logging
import time
from typing import Any, Optional

from msgspec import ValidationError

from zero import config
from zero.codegen.codegen import CodeGen
from zero.encoder.protocols import Encoder
from zero.error import SERVER_PROCESSING_ERROR
from zero.utils.async_to_sync import async_to_sync
from zero.zeromq_patterns.factory import get_worker


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
        worker = get_worker(config.ZEROMQ_PATTERN, worker_id)
        try:
            worker.listen(self._device_comm_channel, self.handle_msg)

        except KeyboardInterrupt:
            logging.warning(
                "Caught KeyboardInterrupt, terminating worker %d", worker_id
            )

        except Exception as exc:  # pylint: disable=broad-except
            logging.exception(exc)

        finally:
            logging.warning("Closing worker %d", worker_id)
            worker.close()

    def handle_msg(self, func_name_encoded: bytes, data: bytes) -> Optional[bytes]:
        try:
            func_name = func_name_encoded.decode()
            input_type = self._rpc_input_type_map.get(func_name)

            msg = ""
            if data:
                if input_type:
                    msg = self._encoder.decode_type(data, input_type)
                else:
                    msg = self._encoder.decode(data)

            response = self.execute_rpc(func_name, msg)
            return self._encoder.encode(response)

        except ValidationError as exc:
            logging.exception(exc)
            return self._encoder.encode({"__zerror__validation_error": str(exc)})

        except Exception as inner_exc:  # pylint: disable=broad-except
            logging.exception(inner_exc)
            return self._encoder.encode(
                {"__zerror__server_exception": SERVER_PROCESSING_ERROR}
            )

    def execute_rpc(self, rpc: str, msg: Any):
        if rpc == "get_rpc_contract":
            return self.generate_rpc_contract(msg)

        if rpc == "connect":
            return "connected"

        if rpc not in self._rpc_router:
            logging.error("Function `%s` not found!", rpc)
            return {"__zerror__function_not_found": f"Function `{rpc}` not found!"}

        func, is_coro = self._rpc_router[rpc]
        ret = None

        try:
            func_to_call = async_to_sync(func) if is_coro else func
            if self._rpc_input_type_map.get(rpc):
                ret = func_to_call(msg)
            else:
                ret = func_to_call()

        except Exception as exc:  # pylint: disable=broad-except
            logging.exception(exc)
            ret = {"__zerror__server_exception": repr(exc)}

        return ret

    def generate_rpc_contract(self, msg):
        try:
            return self.codegen.generate_code(msg[0], msg[1])

        except Exception as exc:  # pylint: disable=broad-except
            logging.exception(exc)
            return {"__zerror__failed_to_generate_client_code": str(exc)}

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
