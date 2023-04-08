import logging

from sanic import Sanic
from sanic.response import json, text

from zero import AsyncZeroClient, ZeroClient

# TODO: why we can't use uvloop?
try:
    import uvloop

    uvloop.install()
except ImportError:
    logging.warning("Cannot use uvloop")
    pass


app = Sanic(__name__)

client = ZeroClient("server", 5559)
async_client = AsyncZeroClient("server", 5559)


@app.route("/hello")
async def hello(request):
    resp = client.call("hello_world", None)
    return text(resp)


@app.route("/async_hello")
async def async_hello(request):
    resp = await async_client.call("hello_world", None)
    return text(resp)


@app.route("/order")
async def order(request):
    resp = client.call("save_order", {"user_id": "1", "items": ["apple", "python"]})
    return json(await resp.json())


@app.route("/async_order")
async def async_order(request):
    resp = await async_client.call(
        "save_order", {"user_id": "1", "items": ["apple", "python"]}
    )
    return json(await resp.json())


@app.route("/jwt")
async def enc_dec_jwt(request):
    resp = await async_client.call("decode_jwt", {"user_id": "a1b2c3"})
    return json(await resp.json())


@app.route("/echo")
async def echo(request):
    big_list = ["hello world" for i in range(100_000)]
    resp = await async_client.call("echo", big_list)
    return text(await resp.text())
