import inspect
import logging
import uuid
from datetime import datetime

import jwt

# from benchmarks.async_redis_repository import save_order as saveOrder
from benchmarks.redis_repository import save_order as saveOrder
from benchmarks.model import Order, OrderStatus, OrderResp, CreateOrderReqQuickle, CreateOrderReq
from zero import ZeroServer


async def echo(msg):
    return msg


async def hello_world(msg):
    return "hello world"


def save_order(msg: CreateOrderReqQuickle):
    req = CreateOrderReq(**msg)
    # req = msg
    saved_order = saveOrder(
        Order(
            id=str(uuid.uuid4()),
            created_by=req.user_id,
            items=req.items,
            created_at=datetime.now().isoformat(),
            status=OrderStatus.INITIATED
        )
    )

    resp = OrderResp(saved_order.id, saved_order.status, saved_order.items)
    return resp.__dict__
    # return req


def decode_jwt(msg):
    encoded_jwt = jwt.encode(msg, 'secret', algorithm='HS256')
    decoded_jwt = jwt.decode(encoded_jwt, 'secret', algorithms=['HS256'])
    logging.info(decoded_jwt)
    return decoded_jwt


if __name__ == "__main__":
    app = ZeroServer(port=5559)
    app.register_rpc(echo)
    app.register_rpc(hello_world)
    app.register_rpc(save_order)
    app.register_rpc(decode_jwt)
    # app.register_msg_types([CreateOrderReqQuickle])
    app.run()
