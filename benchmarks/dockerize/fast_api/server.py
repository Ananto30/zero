import logging
import typing
import uuid
from datetime import datetime

from fastapi import FastAPI
from pydantic import BaseModel

from shared import Order, OrderResp, OrderStatus, async_save_order


logger = logging.getLogger(__name__)

try:
    import uvloop

    uvloop.install()
except ImportError:
    logger.warn("Cannot use uvloop")
    pass


class Request(BaseModel):
    user_id: str
    items: typing.List


app = FastAPI()


@app.get("/hello")
async def hello():
    return "hello world"


@app.post("/order")
async def save_order(req: Request):
    saved_order = await async_save_order(
        Order(
            id=str(uuid.uuid4()),
            created_by=req.user_id,
            items=req.items,
            created_at=datetime.now().isoformat(),
            status=OrderStatus.INITIATED,
        )
    )

    resp = OrderResp(saved_order.id, saved_order.status, saved_order.items)
    return resp.__dict__
