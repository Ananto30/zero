import uuid
from datetime import datetime

from sanic import Sanic
from sanic.response import json, text

from app.serializers import OrderResp, Btype
from benchmarks.async_redis_repository import save_order
from benchmarks.model import Order, OrderStatus

app = Sanic("My Hello, world app")


@app.get("/order")
async def root(request):
    saved_order = await save_order(
        Order(
            id=str(uuid.uuid4()),
            created_by="1",
            items=["apple", "python"],
            created_at=datetime.now().isoformat(),
            status=OrderStatus.INITIATED
        )
    )

    resp = OrderResp(saved_order.id, saved_order.status, saved_order.items)
    print(f"Request served - {Btype.get_all_vars(resp)}")
    return json({
        "id": resp.order_id,
        "status": resp.status,
        "items": resp.items
    })


@app.route('/hello')
async def test(request):
    return text("hello world")


if __name__ == '__main__':
    app.run()
