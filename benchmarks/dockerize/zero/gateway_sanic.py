import logging

from sanic import Sanic
from sanic.response import json, text

from zero import ZeroClient

# TODO: why we can't use uvloop?
try:
    import uvloop

    uvloop.install()
except ImportError:
    logging.warn("Cannot use uvloop")
    pass


app = Sanic(__name__)

zero_sync_client = None
zero_async_client = None


@app.route("/hello")
async def hello(request):
    global zero_sync_client
    if zero_sync_client is None:
        zero_sync_client = ZeroClient("worker", "5559", use_async=False)

    resp = zero_sync_client.call("hello_world", None)
    return text(resp)


@app.route("/async_hello")
async def async_hello(request):
    global zero_async_client
    if zero_async_client is None:
        zero_async_client = ZeroClient("worker", "5559", use_async=True)

    resp = await zero_async_client.call_async("hello_world", None)
    return text(resp)


@app.route("/order")
async def order(request):
    resp = zero_sync_client.call("save_order", {"user_id": "1", "items": ["apple", "python"]})
    # print(resp)
    return json(await resp.json())


@app.route("/async_order")
async def async_order(request):
    resp = await zero_async_client.call_async("save_order", {"user_id": "1", "items": ["apple", "python"]})
    # print(resp)
    return json(await resp.json())


@app.route("/jwt")
async def enc_dec_jwt(request):
    resp = await zero_async_client.call_async("decode_jwt", {"user_id": "a1b2c3"})
    # print(resp)
    # encoded_jwt = jwt.encode({'user_id': 'a1b2c3'}, 'secret', algorithm='HS256')
    # resp = await zero_client.call_async("decode_jwt", encoded_jwt)
    return json(await resp.json())


@app.route("/echo")
async def echo(request):
    big_list = ["hello world" for i in range(100_000)]
    resp = await zero_async_client.call_async("echo", big_list)
    # print(resp)
    return text(await resp.text())
