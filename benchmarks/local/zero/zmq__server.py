import uuid
from datetime import datetime

from shared import CreateOrderReq, Order, OrderResp, OrderStatus
from shared import async_save_order as asyncSaveOrder
from shared import save_order as saveOrder

from zero import ZeroServer

app = ZeroServer(port=5559)


@app.register_rpc
def hello_world() -> str:
    return "hello world"


@app.register_rpc
def save_order(msg: dict) -> dict:
    req = CreateOrderReq(**msg)
    saved_order = saveOrder(
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


@app.register_rpc
async def async_hello_world() -> str:
    return "hello async world"


@app.register_rpc
async def async_save_order(msg: dict) -> dict:
    req = CreateOrderReq(**msg)
    saved_order = await asyncSaveOrder(
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


if __name__ == "__main__":
    app.run()
