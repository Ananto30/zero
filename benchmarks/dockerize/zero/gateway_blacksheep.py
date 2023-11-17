import logging

from blacksheep import Application
from blacksheep import json as json_resp
from blacksheep import text

from zero import AsyncZeroClient, ZeroClient

# TODO: why we can't use uvloop?
try:
    import uvloop

    uvloop.install()
except ImportError:
    logging.warning("Cannot use uvloop")
    pass


app = Application()
get = app.router.get

client = ZeroClient("server", 5559)
async_client = AsyncZeroClient("server", 5559)


@get("/hello")
async def hello():
    resp = client.call("hello_world", None)
    return text(resp)


@get("/async_hello")
async def async_hello():
    resp = await async_client.call("hello_world", None)
    return text(resp)


@get("/order")
async def order():
    resp = client.call("save_order", {"user_id": "1", "items": ["apple", "python"]})
    return json_resp(resp)


@get("/async_order")
async def async_order():
    resp = await async_client.call(
        "save_order", {"user_id": "1", "items": ["apple", "python"]}
    )
    return json_resp(resp)
