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
            if IS_PYDANTIC_V2:
                data = data.model_dump()
            else:  # Pydantic v1
                data = data.dict()

        return super().encode(data)

    def decode_type(self, data: bytes, typ: Type[T]) -> T:
        if PYDANTIC_AVAILABLE and issubclass(typ, BaseModel):
            data = self.decode(data)
            if IS_PYDANTIC_V2:
                return typ.model_validate(data)  # type: ignore[return-value]
            else:  # Pydantic v1
                return typ.parse_obj(data)  # type: ignore[return-value]

        return super().decode_type(data, typ)
