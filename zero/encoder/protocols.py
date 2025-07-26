from typing import Any, Protocol, Type, runtime_checkable


@runtime_checkable
class Encoder(Protocol):  # pragma: no cover
    def encode(self, data: Any) -> bytes:
        ...

    def decode(self, data: bytes) -> Any:
        ...

    def decode_type(self, data: bytes, typ: Type[Any]) -> Any:
        ...

    def is_allowed_type(self, typ: Type) -> bool:
        ...
