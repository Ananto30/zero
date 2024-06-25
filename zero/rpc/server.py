import logging
import os
from asyncio import iscoroutinefunction
from typing import TYPE_CHECKING, Callable, Dict, Optional, Tuple, Type

from zero import config
from zero.encoder import Encoder, get_encoder
from zero.utils import type_util

if TYPE_CHECKING:
    from .protocols import ZeroServerProtocol

# import uvloop


class ZeroServer:
    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 5559,
        encoder: Optional[Encoder] = None,
        protocol: str = "zeromq",
    ):
        """
        ZeroServer registers and exposes rpc functions that can be called from a ZeroClient.

        By default ZeroServer uses all of the cores for best performance possible.

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
        protocol: str
            Protocol to use for communication.
            Default is zeromq.
            If any other protocol is used, the client should use the same protocol.
        """
        self._host = host
        self._port = port
        self._address = f"tcp://{self._host}:{self._port}"

        # to encode/decode messages from/to client
        self._encoder = encoder or get_encoder(config.ENCODER)

        # Stores rpc functions against their names
        # and if they are coroutines
        self._rpc_router: Dict[str, Tuple[Callable, bool]] = {}

        # Stores rpc functions `msg` types
        self._rpc_input_type_map: Dict[str, Optional[type]] = {}
        self._rpc_return_type_map: Dict[str, Optional[type]] = {}

        self._server_inst: "ZeroServerProtocol" = self._determine_server_cls(protocol)(
            self._address,
            self._rpc_router,
            self._rpc_input_type_map,
            self._rpc_return_type_map,
            self._encoder,
        )

    def _determine_server_cls(self, protocol: str) -> Type["ZeroServerProtocol"]:
        if protocol not in config.SUPPORTED_PROTOCOLS:
            raise ValueError(
                f"Protocol {protocol} is not supported. "
                f"Supported protocols are {config.SUPPORTED_PROTOCOLS}"
            )
        server_cls = config.SUPPORTED_PROTOCOLS.get(protocol, {}).get("server")
        if not server_cls:
            raise ValueError(
                f"Protocol {protocol} is not supported. "
                f"Supported protocols are {config.SUPPORTED_PROTOCOLS}"
            )
        return server_cls

    def register_rpc(self, func: Callable):
        """
        Register a function available for clients.
        Function should have a single argument.
        Argument and return should have a type hint.

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

        self._rpc_router[func.__name__] = (func, iscoroutinefunction(func))
        return func

    def run(self, workers: int = os.cpu_count() or 1):
        """
        Run the ZeroServer. This is a blocking operation.
        By default it uses all the cores available.

        Ensure to run the server inside
        `if __name__ == "__main__":`
        As the server runs on multiple processes.

        Parameters
        ----------
        workers: int
            Number of workers to spawn.
            Each worker is a zmq router and runs on a separate process.
        """
        try:
            self._server_inst.start(workers)
        except KeyboardInterrupt:
            logging.warning("Caught KeyboardInterrupt, terminating server")
        except Exception as exc:  # pylint: disable=broad-except
            logging.exception(exc)
        finally:
            self._server_inst.stop()

    def _verify_function_name(self, func):
        if not isinstance(func, Callable):
            raise ValueError(f"register function; not {type(func)}")
        if len(func.__name__) > 80:
            raise ValueError(
                "function name can be at max 80" f" characters; {func.__name__}"
            )
        if func.__name__ in self._rpc_router:
            raise ValueError(
                f"cannot have two RPC function same name: `{func.__name__}`"
            )
        if func.__name__ in config.RESERVED_FUNCTIONS:
            raise ValueError(
                f"{func.__name__} is a reserved function; cannot have `{func.__name__}` "
                "as a RPC function"
            )
