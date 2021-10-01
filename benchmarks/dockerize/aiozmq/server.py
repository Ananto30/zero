import asyncio
import uuid
from datetime import datetime

import aiozmq.rpc
from shared import CreateOrderReq, Order, OrderResp, OrderStatus, async_save_order
from shared import save_order as saveOrder


class ServerHandler(aiozmq.rpc.AttrHandler):
    @aiozmq.rpc.method
    async def hello_world(self) -> str:
        return "hello world"

    @aiozmq.rpc.method
    async def save_order(self, msg: dict) -> dict:
        req = CreateOrderReq(**msg)
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


async def go():
    server = await aiozmq.rpc.serve_rpc(ServerHandler(), bind="tcp://0.0.0.0:5555")
    while True:
        await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(go())
