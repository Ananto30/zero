import logging

from aiohttp import web

from zero import ZeroClient, ZeroPublisher

# TODO: why we can't use uvloop?
# try:
#     import uvloop

#     uvloop.install()
# except ImportError:
#     logging.warn("Cannot use uvloop")
#     pass

zero_sync_client = ZeroClient("localhost", "5559", use_async=False)
zero_publisher = ZeroPublisher("localhost", "5558", use_async=True)
zero_async_client = ZeroClient("localhost", "5559", use_async=True)


async def hello(request):
    resp = await zero_async_client.call_async("hello_world", None)
    # print(resp)
    return web.Response(text=resp)


async def order(request):
    resp = zero_sync_client.call(
        "save_order", {"user_id": "1", "items": ["apple", "python"]}
    )
    # print(resp)
    return web.json_response(resp)


async def async_order(request):
    resp = await zero_async_client.call_async(
        "save_order", {"user_id": "1", "items": ["apple", "python"]}
    )
    # print(resp)
    return web.json_response(resp)


async def pubs(request):
    await zero_publisher.publish_async("hello_world", {"1": {"2": {"3": {"4": "5"}}}})
    return web.Response()


async def enc_dec_jwt(request):
    resp = await zero_async_client.call_async("decode_jwt", {"user_id": "a1b2c3"})
    # print(resp)
    # encoded_jwt = jwt.encode({'user_id': 'a1b2c3'}, 'secret', algorithm='HS256')
    # resp = await zero_client.call_async("decode_jwt", encoded_jwt)
    return web.json_response(resp)


async def echo(request):
    big_list = ["hello world" for i in range(100_000)]
    resp = await zero_async_client.call_async("echo", big_list)
    # print(resp)
    return web.Response(text=str(resp))


async def gateway_app():
    app = web.Application()
    app.router.add_get("/order", order)
    app.router.add_get("/async_order", async_order)
    app.router.add_get("/hello", hello)
    app.router.add_get("/pub", pubs)
    app.router.add_get("/echo", echo)
    app.router.add_get("/jwt", enc_dec_jwt)
    return app
