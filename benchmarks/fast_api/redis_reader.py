import typing
import uuid
from datetime import datetime

from fastapi import FastAPI
from pydantic import BaseModel

from app.serializers import OrderResp, Btype
from benchmarks.async_redis_repository import save_order
from benchmarks.model import Order, OrderStatus


class Request(BaseModel):
    user_id: str
    items: typing.List


app = FastAPI()


@app.get("/")
async def root():
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
    return {
        "id": resp.order_id,
        "status": resp.status,
        "items": resp.items
    }


@app.post("/order")
async def root(req: Request):
    saved_order = await save_order(
        Order(
            id=str(uuid.uuid4()),
            created_by=req.user_id,
            items=req.items,
            created_at=datetime.now().isoformat(),
            status=OrderStatus.INITIATED
        )
    )

    resp = OrderResp(saved_order.id, saved_order.status, saved_order.items)
    print(f"Request served - {Btype.get_all_vars(resp)}")
    return {
        "id": resp.order_id,
        "status": resp.status,
        "items": resp.items
    }
