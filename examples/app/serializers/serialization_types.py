from typing import Optional, Any
from dataclasses import dataclass

import msgpack


@dataclass
class Btype:
    def pack(self):
        return msgpack.packb(Btype.get_all_vars(self))

    @classmethod
    def unpack(cls, d):
        return cls(**msgpack.unpackb(d, raw=False))

    @staticmethod
    def get_all_vars(obj):
        values = vars(obj)
        for k, v in values.items():
            if isinstance(v, Btype):
                values[k] = vars(v)
        return values


@dataclass
class Etype(Btype):
    request: dict
    operation: str
    response: Optional[Any] = None
