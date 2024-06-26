import logging
from typing import List

from src.store import create_order, get_order_by_id, get_orders_by_user_id

from zero import ZeroServer

log = logging.getLogger("OrderService")


async def add_order(msg: dict) -> bool:
    """
    Create a new order for the given user.
    """
    try:
        await create_order(msg.get("user_id"), msg.get("items"))
        return True
    except Exception as e:
        log.error(f"Failed to create order: {e}")
        return False


async def get_order(order_id: int) -> dict:
    """
    Get the order with the given ID.
    """
    order = await get_order_by_id(order_id)
    if order:
        return order
    else:
        return {"error": "Order not found"}


async def get_orders(user_id: int) -> List[dict]:
    """
    Get all orders for the given user.
    """
    return await get_orders_by_user_id(user_id)


if __name__ == "__main__":
    app = ZeroServer(port=6002)
    app.register_rpc(add_order)
    app.register_rpc(get_order)
    app.register_rpc(get_orders)
    app.run()
