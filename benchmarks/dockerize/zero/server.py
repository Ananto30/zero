import logging
import uuid
from datetime import datetime

import jwt
from shared import CreateOrderReq, Order, OrderResp, OrderStatus, async_save_order
from shared import save_order as saveOrder

from zero import ZeroServer


async def echo(msg: str) -> str:
    return msg


def hello_world() -> str:
    return "hello world"


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


def decode_jwt(msg: str) -> str:
    encoded_jwt = jwt.encode(msg, "secret", algorithm="HS256")
    decoded_jwt = jwt.decode(encoded_jwt, "secret", algorithms=["HS256"])
    logging.info(decoded_jwt)
    return decoded_jwt


if __name__ == "__main__":
    app = ZeroServer(port=5559)
    app.register_rpc(echo)
    app.register_rpc(hello_world)
    app.register_rpc(save_order)
    app.register_rpc(decode_jwt)
    app.run()
