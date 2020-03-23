import uuid
from datetime import datetime

from app.serializers import CreateOrderReq, OrderResp, GetOrderReq

from .model import Order, OrderStatus
from .repository import save_order, get_order as query_order


def create_order(req: CreateOrderReq) -> OrderResp:
    saved_order = save_order(
        Order(
            id=str(uuid.uuid4()),
            created_by=req.user_id,
            items=req.items,
            created_at=datetime.now().isoformat(),
            status=OrderStatus.INITIATED
        )
    )

    return OrderResp(saved_order.id, saved_order.status, saved_order.items)


def get_order(req: GetOrderReq) -> OrderResp:
    order = query_order(req.order_id)

    return OrderResp(order.id, order.status, order.items)
