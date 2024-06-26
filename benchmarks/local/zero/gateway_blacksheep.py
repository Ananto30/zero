from blacksheep import Application, json, text

from zero import AsyncZeroClient, ZeroClient

client = ZeroClient("server", 5559)
async_client = AsyncZeroClient("server", 5559)

app = Application()
get = app.router.get


@get("/hello")
def hello():
    resp = client.call("hello_world", None)
    return text(resp)


@get("/async_hello")
async def async_hello():
    resp = await async_client.call("hello_world", None)
    return text(resp)


@get("/order")
def order():
    resp = client.call("save_order", {"user_id": "1", "items": ["apple", "python"]})
    return json(resp)


@get("/async_order")
async def async_order():
    resp = await async_client.call("save_order", {"user_id": "1", "items": ["apple", "python"]})
    return json(resp)
