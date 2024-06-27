from typing import (
    Callable,
    Dict,
    Optional,
    Protocol,
    Tuple,
    Type,
    TypeVar,
    runtime_checkable,
)

from zero.encoder import Encoder
from zero.utils.type_util import AllowedType

T = TypeVar("T")


@runtime_checkable
class ZeroServerProtocol(Protocol):
    def __init__(
        self,
        address: str,
        rpc_router: Dict[str, Tuple[Callable, bool]],
        rpc_input_type_map: Dict[str, Optional[type]],
        rpc_return_type_map: Dict[str, Optional[type]],
        encoder: Encoder,
    ):
        ...

    def start(self, workers: int):
        ...

    def stop(self):
        ...


@runtime_checkable
class ZeroClientProtocol(Protocol):
    def __init__(
        self,
        address: str,
        default_timeout: int,
        encoder: Encoder,
    ):
        ...

    def call(
        self,
        rpc_func_name: str,
        msg: AllowedType,
        timeout: Optional[int] = None,
        return_type: Optional[Type[T]] = None,
    ) -> Optional[T]:
        ...

    def close(self):
        ...


@runtime_checkable
class AsyncZeroClientProtocol(Protocol):
    def __init__(
        self,
        address: str,
        default_timeout: int,
        encoder: Encoder,
    ):
        ...

    async def call(
        self,
        rpc_func_name: str,
        msg: AllowedType,
        timeout: Optional[int] = None,
        return_type: Optional[Type[T]] = None,
    ) -> Optional[T]:
        ...

    async def close(self):
        ...
