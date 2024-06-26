from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class Encoder(Protocol):  # pragma: no cover
    def encode(self, data: Any) -> bytes: ...

    def decode(self, data: bytes) -> Any: ...

    def decode_type(self, data: bytes, typ: Any) -> Any: ...
