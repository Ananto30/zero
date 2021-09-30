from datetime import datetime

import redis

from model import Order


class SingletonMeta(type):
    _instance = None

    def __call__(self):
        if self._instance is None:
            self._instance = super().__call__()
        return self._instance


class RedisClient(metaclass=SingletonMeta):
    def __init__(self):
        self.host = "0.0.0.0"
        self.client = redis.StrictRedis().from_url("redis://127.0.0.1/0")

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
