import logging

from sanic import Sanic
from sanic.response import json, text

from zero import AsyncZeroClient
from zero.protocols.tcp import AsyncTCPClient

# TODO: why we can't use uvloop?
try:
    import uvloop

    uvloop.install()
except ImportError:
    logging.warning("Cannot use uvloop")
    pass


app = Sanic(__name__)

async_client = AsyncZeroClient(
    "server",
    5559,
    protocol=AsyncTCPClient,
    pool_size=100,
)


@app.route("/async_hello")
async def async_hello(request):
    resp = await async_client.call("async_hello_world", None)
    return text(resp)


@app.route("/async_order")
async def async_order(request):
    resp = await async_client.call(
        "async_save_order", {"user_id": "1", "items": ["apple", "python"]}
    )
    return json(resp)
