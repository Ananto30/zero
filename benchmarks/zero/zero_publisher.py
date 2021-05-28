import logging
import uuid
from datetime import datetime

from benchmarks.async_redis_repository import save_order as saveOrder
from benchmarks.model import Order, OrderStatus, OrderResp, CreateOrderReq
from zero import ZeroSubscriber


async def hello_world(msg):
    logging.info(msg)


async def save_order(msg):
    req = CreateOrderReq(**msg)
    saved_order = await saveOrder(
        Order(
            id=str(uuid.uuid4()),
            created_by=req.user_id,
            items=req.items,
            created_at=datetime.now().isoformat(),
            status=OrderStatus.INITIATED
        )
    )

    resp = OrderResp(saved_order.id, saved_order.status, saved_order.items)
    return resp.__dict__


if __name__ == "__main__":
    app = ZeroSubscriber()
    app.register_listener("hello_world", hello_world)
    app.register_listener("save_order", save_order)
    app.run()
