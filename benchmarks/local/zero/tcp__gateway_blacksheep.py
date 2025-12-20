from blacksheep import Application, json, text

from zero import AsyncZeroClient
from zero.protocols.tcp import AsyncTCPClient

async_client = AsyncZeroClient(
    "server",
    5559,
    protocol=AsyncTCPClient,
    pool_size=100,
)

app = Application()
get = app.router.get


@get("/async_hello")
async def async_hello():
    resp = await async_client.call("async_hello_world", None)
    return text(resp)


@get("/async_order")
async def async_order():
    resp = await async_client.call(
        "async_save_order", {"user_id": "1", "items": ["apple", "python"]}
    )
    return json(resp)
