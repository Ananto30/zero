from zero import AsyncZeroClient, ZeroClient, ZeroServer

client = ZeroClient("localhost", 7777)
async_client = AsyncZeroClient("localhost", 7777)


def echo(msg: str) -> str:
    return client.call("echo", msg)


def hello() -> str:
    return client.call("hello", None)


async def async_echo(msg: str) -> str:
    return await async_client.call("echo", msg)


async def async_hello() -> str:
    return await async_client.call("hello", None)


def run(port):
    print("Starting server2 on port", port)
    app = ZeroServer(port=port)
    app.register_rpc(echo)
    app.register_rpc(hello)
    app.register_rpc(async_echo)
    app.register_rpc(async_hello)
    app.run()
