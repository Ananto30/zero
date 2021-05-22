import uuid
from datetime import datetime

from aiohttp import web

from app.serializers import OrderResp, Btype
from benchmarks.async_redis_repository import save_order
from benchmarks.model import Order, OrderStatus


# from benchmarks.redis_repository import save_order


async def hello(request):
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
    return web.json_response({
        "id": resp.order_id,
        "status": resp.status,
        "items": resp.items
    })


async def order(request):
    body = await request.json()
    saved_order = await save_order(
        Order(
            id=str(uuid.uuid4()),
            created_by=body['user_id'],
            items=body['items'],
            created_at=datetime.now().isoformat(),
            status=OrderStatus.INITIATED
        )
    )

    resp = OrderResp(saved_order.id, saved_order.status, saved_order.items)
    print(f"Request served - {Btype.get_all_vars(resp)}")
    return web.json_response({
        "id": resp.order_id,
        "status": resp.status,
        "items": resp.items
    })


async def redis_app():
    app = web.Application()
    app.router.add_get('/', hello)
    app.router.add_post("/order", order)
    return app
