import logging

from sanic import Sanic
from sanic.response import json, text

from zero import AsyncZeroClient, ZeroClient
from zero.protocols.tcp import AsyncTCPClient

try:
    import uvloop

    uvloop.install()
except ImportError:
    logging.warning("Cannot use uvloop")


app = Sanic(__name__)

client = ZeroClient("server", 5559)
async_client = AsyncZeroClient("server", 5559, protocol=AsyncTCPClient, pool_size=100)


@app.route("/async_hello")
async def async_hello(request):
    resp = await async_client.call("hello_world", None)
    return text(resp)


@app.route("/async_order")
async def async_order(request):
    resp = await async_client.call(
        "save_order", {"user_id": "1", "items": ["apple", "python"]}
    )
    return json(resp)
