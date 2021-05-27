from .model import Order
from datetime import datetime


def save_order(order: Order) -> Order:
    order.updated_at = datetime.now().isoformat()
    Order.orders[order.id] = order
    return order


def get_order(id: str) -> Order:
    return Order.orders[id]
