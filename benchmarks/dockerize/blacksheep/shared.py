from dataclasses import dataclass
from datetime import datetime

import aioredis
import msgpack
import redis


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


class SingletonMeta(type):
    _instance = None

    def __call__(self):
        if self._instance is None:
            self._instance = super().__call__()
        return self._instance


class AsyncRedisClient(metaclass=SingletonMeta):
    def __init__(self):
        self.client = aioredis.from_url("redis://redis:6379/0")

    async def set(self, key, val):
        await self.client.set(key, val)

    async def get(self, key):
        return await self.client.get(key)


async def async_save_order(order: Order) -> Order:
    order.updated_at = datetime.now().isoformat()
    r = AsyncRedisClient()
    await r.set(order.id, order.pack())
    return order


async def async_get_order(id: str) -> Order:
    r = AsyncRedisClient()
    return Order.unpack(await r.get(id))


class SingletonMeta(type):
    _instance = None

    def __call__(self):
        if self._instance is None:
            self._instance = super().__call__()
        return self._instance


class RedisClient(metaclass=SingletonMeta):
    def __init__(self):
        self.host = "0.0.0.0"
        self.client = redis.StrictRedis().from_url("redis://redis:6379/0")

    def set(self, key, val):
        self.client.set(key, val)

    def get(self, key):
        return self.client.get(key)


def save_order(order: Order) -> Order:
    order.updated_at = datetime.now().isoformat()
    r = RedisClient()
    r.set(order.id, order.pack())
    return order


def get_order(id: str) -> Order:
    r = RedisClient()
    return Order.unpack(r.get(id))
