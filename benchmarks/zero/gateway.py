from aiohttp import web

from zero import ZeroClient, ZeroPublisher

zero_client = ZeroClient("localhost", "5559", use_async=True)
zero_publisher = ZeroPublisher("localhost", "5558", use_async=True)


async def hello(request):
    msg = await zero_client.call_async("hello_world", "")
    print(msg)
    return web.Response(text=msg)


async def order(request):
    msg = await zero_client.call_async("save_order", {"user_id": "1", "items": ['apple', 'python']})
    # print(msg)
    return web.json_response(msg)


async def pubs(request):
    await zero_publisher.publish_async("hello_world", {'1': {'2': {'3': {'4': '5'}}}})
    return web.Response()


async def gateway_app():
    app = web.Application()
    app.router.add_get('/', order)
    app.router.add_get('/hello', hello)
    app.router.add_get('/pub', pubs)
    return app
