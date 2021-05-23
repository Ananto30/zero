import uuid
from datetime import datetime

from app.serializers import OrderResp
from benchmarks.async_redis_repository import save_order as saveOrder
from benchmarks.model import Order, OrderStatus
from zero import Zero

app = Zero()


async def hello_world(msg):
    return "hello world"


async def save_order(msg):
    saved_order = await saveOrder(
        Order(
            id=str(uuid.uuid4()),
            created_by="1",
            items=["apple", "python"],
            created_at=datetime.now().isoformat(),
            status=OrderStatus.INITIATED
        )
    )

    resp = OrderResp(saved_order.id, saved_order.status, saved_order.items)
    # return {
    #     "id": resp.order_id,
    #     "status": resp.status,
    #     "items": resp.items
    # }
    return resp.__dict__


if __name__ == "__main__":
    app.register_rpc("hello_world", hello_world)
    app.register_rpc("save_order", save_order)
    app.run()
