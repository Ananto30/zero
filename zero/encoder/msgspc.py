from typing import Any, Type, TypeVar

import msgspec

T = TypeVar("T")

# Have to put here to make it fork-safe
encoder = msgspec.msgpack.Encoder()
decoder = msgspec.msgpack.Decoder()


class MsgspecEncoder:
    def __init__(self) -> None:
        pass

    def encode(self, data: Any) -> bytes:
        return encoder.encode(data)

    def decode(self, data: bytes) -> Any:
        return decoder.decode(data)

    def decode_type(self, data: bytes, typ: Type[T]) -> T:
        return msgspec.msgpack.decode(data, type=typ)
