from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class Encoder(Protocol):
    def encode(self, message: Any) -> bytes:
        ...

    def decode(self, message: bytes) -> Any:
        ...
