from datetime import datetime

import aioredis

from .model import Order


class SingletonMeta(type):
    _instance = None

    def __call__(self):
        if self._instance is None:
            self._instance = super().__call__()
        return self._instance


class RedisClient(metaclass=SingletonMeta):
    def __init__(self):
        self.client = aioredis.from_url("redis://localhost")

    async def set(self, key, val):
        await self.client.set(key, val)

    async def get(self, key):
        return await self.client.get(key)


async def save_order(order: Order) -> Order:
    order.updated_at = datetime.now().isoformat()
    r = RedisClient()
    await r.set(order.id, order.pack())
    return order


async def get_order(id: str) -> Order:
    r = RedisClient()
    return Order.unpack(await r.get(id))
