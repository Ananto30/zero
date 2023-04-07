import asyncio
import inspect
import logging
import time
from typing import Optional

from zero import config
from zero.codegen.codegen import CodeGen
from zero.encoder.protocols import Encoder
from zero.zero_mq.factory import get_worker


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

        worker = cls(
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
                response = self.handle_msg(rpc_method, msg)
                return self.encoder.encode([req_id, response])
            except Exception as inner_exc:
                logging.exception(inner_exc)
                # TODO what to return
                return None

        worker = get_worker(config.ZEROMQ_PATTERN, worker_id)
        try:
            worker.listen(self._device_comm_channel, process_message)
        except KeyboardInterrupt:
            logging.info("shutting down worker")
        except Exception as exc:
            logging.exception(exc)
        finally:
            logging.info("closing worker")
            worker.close()

    def handle_msg(self, rpc, msg):
        if rpc == "get_rpc_contract":
            return self.generate_rpc_contract(msg)

        if rpc == "connect":
            return "connected"

        if rpc not in self._rpc_router:
            logging.error("method `%s` is not found!", rpc)
            return {"__zerror__method_not_found": f"method `{rpc}` is not found!"}

        func = self._rpc_router[rpc]
        ret = None

        try:
            # TODO: is this a bottleneck
            if inspect.iscoroutinefunction(func):
                # this is blocking
                ret = self._loop.run_until_complete(func(msg) if msg else func())
            else:
                ret = func(msg) if msg else func()

        except Exception as exc:
            logging.exception(exc)

        return ret

    def generate_rpc_contract(self, msg):
        try:
            return self.codegen.generate_code(msg[0], msg[1])
        except Exception as exc:
            logging.exception(exc)
            return {"__zerror__failed_to_generate_client_code": str(exc)}
