import logging

from aiohttp import web
import aiozmq.rpc

try:
    import uvloop

    uvloop.install()
except ImportError:
    logging.warn("Cannot use uvloop")
    pass

aiozmq_client = None


async def hello(request):
    global aiozmq_client
    if aiozmq_client is None:
        aiozmq_client = await aiozmq.rpc.connect_rpc(connect="tcp://server:5555")

    resp = await aiozmq_client.call.hello_world()
    # print(resp)
    return web.Response(text=resp)


async def save_order(request):
    global aiozmq_client
    if aiozmq_client is None:
        aiozmq_client = await aiozmq.rpc.connect_rpc(connect="tcp://server:5555")

    data = {"user_id": "1", "items": ["apple", "python"]}
    resp = await aiozmq_client.call.save_order(data)
    # print(resp)
    return web.json_response(resp)


app = web.Application()
app.router.add_get("/hello", hello)
app.router.add_get("/order", save_order)
