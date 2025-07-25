from typing import Any, Type

try:
    from pydantic import BaseModel

    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False

from .msgspc import MsgspecEncoder, T


class GenericEncoder(MsgspecEncoder):
    def encode(self, data: Any) -> bytes:
        if PYDANTIC_AVAILABLE and isinstance(
            data, BaseModel
        ):  # pytype: disable=wrong-arg-types
            if hasattr(data, "model_dump"):  # Pydantic v2
                data = data.model_dump()
            else:
                data = data.dict()

        return super().encode(data)

    def decode_type(self, data: bytes, typ: Type[T]) -> T:
        if PYDANTIC_AVAILABLE and issubclass(
            typ, BaseModel
        ):  # pytype: disable=wrong-arg-types
            decoded_data = self.decode(data)
            if hasattr(typ, "model_validate"):  # Pydantic v2
                return typ.model_validate(decoded_data)
            return typ.parse_obj(decoded_data)

        return super().decode_type(data, typ)
