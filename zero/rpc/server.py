import logging
import os
from asyncio import iscoroutinefunction
from typing import (
    Any,
    Callable,
    Coroutine,
    Dict,
    Optional,
    Tuple,
    Type,
    Union,
)

from zero import config
from zero.encoder import Encoder
from zero.encoder.generic import GenericEncoder
from zero.protocols.zeromq.server import ZMQServer
from zero.utils import type_util

from ..protocols.blueprint import ZeroServerProtocol


class ZeroServer:
    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 5559,
        encoder: Type[Encoder] = GenericEncoder,
        protocol: Type[ZeroServerProtocol] = ZMQServer,
        use_threads: bool = False,
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

        encoder: Type[Encoder]
            Encoder class to use for encoding/decoding messages from/to client.
            Default is GenericEncoder with msgspec and pydantic support.
            If any other encoder is used, the client should use the same encoder.
            Implement custom encoder by inheriting from `zero.encoder.Encoder`.

        protocol: Union[Type[ZeroServerProtocol], str]
            Protocol server class to use for communication.
            Default is ZMQServer.
            Can be a protocol class or a string name like "zmq".
            Must implement the ZeroServerProtocol interface.

        use_threads: bool
            Use threads instead of processes.
            By default it uses processes.
            If True, the server uses threads instead of processes. GIL will be watching you!
        """
        self._host = host
        self._port = port
        self._address = f"tcp://{self._host}:{self._port}"
        self._use_threads = use_threads

        # to encode/decode messages from/to client
        if not isinstance(encoder, type) or not issubclass(encoder, Encoder):
            raise TypeError(f"encoder should be a subclass of Encoder; not {encoder}")
        self._encoder = encoder()

        if not isinstance(protocol, type) or not issubclass(
            protocol, ZeroServerProtocol
        ):
            raise TypeError(
                f"protocol should be a subclass of ZeroServerProtocol; not {protocol}"
            )

        # Stores rpc functions against their names
        # and if they are coroutines
        self._rpc_router: Dict[str, Tuple[Callable, bool]] = {}

        # Stores rpc functions `msg` types
        self._rpc_input_type_map: Dict[str, Optional[type]] = {}
        self._rpc_return_type_map: Dict[str, Optional[type]] = {}

        self._server_inst = protocol(
            self._address,
            self._rpc_router,
            self._rpc_input_type_map,
            self._rpc_return_type_map,
            self._encoder,
            self._use_threads,
        )

    def register_rpc(self, func: Callable[..., Union[Any, Coroutine]]):
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
        type_util.verify_function_return(func)
        type_util.verify_function_input_type(func, self._encoder)
        type_util.verify_function_return_type(func, self._encoder)

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
