import logging
from typing import List

from msgspec import Struct
from src.store import create_order, get_order_by_id, get_orders_by_user_id

from zero import ZeroServer
from zero.protocols.tcp import TCPServer

log = logging.getLogger("OrderService")

app = ZeroServer(port=6002, protocol=TCPServer)


class OrderResp(Struct):
    id: int
    user_id: int
    placed_at: str
    items: List[str]
    status: int


class OrderReq(Struct):
    user_id: int
    items: List[str]


@app.register_rpc
async def add_order(req: OrderReq) -> bool:
    """
    Create a new order for the given user.
    """
    await create_order(req.user_id, req.items)
    return True


@app.register_rpc
async def get_order(order_id: int) -> OrderResp:
    """
    Get the order with the given ID.
    """
    order = await get_order_by_id(order_id)
    if not order:
        raise ValueError(f"Order with id {order_id} not found")
    return OrderResp(**order)


@app.register_rpc
async def get_orders(user_id: int) -> List[OrderResp]:
    """
    Get all orders for the given user.
    """
    orders = await get_orders_by_user_id(user_id)
    return [OrderResp(**order) for order in orders]


if __name__ == "__main__":
    app.run(workers=2)
