import logging
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import List

from blacksheep import Application, FromJSON, json, text
from shared import Order, OrderResp, OrderStatus, async_save_order

app = Application()
get = app.router.get
post = app.router.post

logger = logging.getLogger(__name__)

try:
    import uvloop

    uvloop.install()
except ImportError:
    logger.warning("Cannot use uvloop")


@get("/hello")
async def hello():
    return text("hello world")


@get("/order")
async def get_order():
    saved_order = await async_save_order(
        Order(
            id=str(uuid.uuid4()),
            created_by="1",
            items=["apple", "python"],
            created_at=datetime.now().isoformat(),
            status=OrderStatus.INITIATED,
        )
    )

    resp = OrderResp(
        saved_order.id,
        saved_order.status,
        saved_order.items,
    )
    return json(
        {
            "id": resp.order_id,
            "status": resp.status,
            "items": resp.items,
        }
    )


@dataclass
class OrderReq:
    user_id: str
    items: List[str]


@post("/order")
async def order(req: FromJSON[OrderReq]):
    body = req.value
    saved_order = await async_save_order(
        Order(
            id=str(uuid.uuid4()),
            created_by=body.user_id,
            items=body.items,
            created_at=datetime.now().isoformat(),
            status=OrderStatus.INITIATED,
        )
    )

    resp = OrderResp(
        saved_order.id,
        saved_order.status,
        saved_order.items,
    )
    return json(
        {
            "id": resp.order_id,
            "status": resp.status,
            "items": resp.items,
        }
    )
