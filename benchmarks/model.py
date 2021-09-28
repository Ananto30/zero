from dataclasses import dataclass

import msgpack
from pydantic import BaseModel


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


class OrderStatus:
    INITIATED = 0
    PACKING = 1
    SHIPPED = 2
    DELIVERED = 3


class Order(Btype):
    # cache
    orders = {}

    def __init__(self, id, items, created_by, created_at, status, updated_at=None):
        self.id = id
        self.items = items
        self.created_by = created_by
        self.created_at = created_at
        self.status = status
        self.updated_at = updated_at


@dataclass
class OrderResp(Btype):
    order_id: str
    status: int
    items: list


@dataclass
class CreateOrderReq(Btype):
    user_id: str
    items: list


