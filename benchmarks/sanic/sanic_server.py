import uuid
from datetime import datetime

from sanic import Sanic
from sanic.response import json, text

from benchmarks.async_redis_repository import save_order
from benchmarks.model import Order, OrderStatus, OrderResp

app = Sanic("My Hello, world app")


@app.post("/order")
async def root(request):
    body = request.json
    saved_order = await save_order(
        Order(
            id=str(uuid.uuid4()),
            created_by=body["user_id"],
            items=body["items"],
            created_at=datetime.now().isoformat(),
            status=OrderStatus.INITIATED,
        )
    )

    resp = OrderResp(saved_order.id, saved_order.status, saved_order.items)
    return json({"id": resp.order_id, "status": resp.status, "items": resp.items})


@app.route("/hello")
async def test(request):
    return text("hello world")


if __name__ == "__main__":
    app.run()
