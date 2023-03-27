from typing import Any, Protocol


class Encoder(Protocol):
    def encode(self, message: Any) -> bytes:
        ...

    def decode(self, message: bytes) -> Any:
        ...
