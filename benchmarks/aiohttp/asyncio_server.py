import uuid
import logging
from datetime import datetime

from aiohttp import web

from benchmarks.async_redis_repository import save_order
from benchmarks.model import Order, OrderStatus, OrderResp

# from benchmarks.redis_repository import save_order

logger = logging.getLogger(__name__)

try:
    import uvloop

    uvloop.install()
except ImportError:
    logger.warn("Cannot use uvloop")
    pass


async def hello(request):
    return web.Response(text="hello world")


async def get_order(request):
    saved_order = await save_order(
        Order(
            id=str(uuid.uuid4()),
            created_by="1",
            items=["apple", "python"],
            created_at=datetime.now().isoformat(),
            status=OrderStatus.INITIATED,
        )
    )

    resp = OrderResp(saved_order.id, saved_order.status, saved_order.items)
    return web.json_response(
        {"id": resp.order_id, "status": resp.status, "items": resp.items}
    )


async def order(request):
    body = await request.json()
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
    return web.json_response(
        {"id": resp.order_id, "status": resp.status, "items": resp.items}
    )


async def aiohttp_app():
    app = web.Application()
    app.router.add_get("/order", get_order)
    app.router.add_post("/order", order)
    app.router.add_get("/hello", hello)
    return app
