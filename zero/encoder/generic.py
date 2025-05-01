from typing import Any, Type

try:
    from pydantic import VERSION, BaseModel

    PYDANTIC_AVAILABLE = True
    IS_PYDANTIC_V2 = VERSION.startswith("2.")
except ImportError:
    PYDANTIC_AVAILABLE = False
    IS_PYDANTIC_V2 = False

from .msgspc import MsgspecEncoder, T


class GenericEncoder(MsgspecEncoder):
    def encode(self, data: Any) -> bytes:
        if PYDANTIC_AVAILABLE and isinstance(data, BaseModel):
            data = data.model_dump() if IS_PYDANTIC_V2 else data.dict()

        return super().encode(data)

    def decode_type(self, data: bytes, typ: Type[T]) -> T:
        if PYDANTIC_AVAILABLE and issubclass(typ, BaseModel):
            decoded_data = self.decode(data)
            return (
                typ.model_validate(decoded_data)  # type: ignore[return-value]
                if IS_PYDANTIC_V2
                else typ.parse_obj(decoded_data)
            )

        return super().decode_type(data, typ)
