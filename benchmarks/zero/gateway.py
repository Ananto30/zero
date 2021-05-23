from aiohttp import web

from zero import ZeroClient

zero_client = ZeroClient("localhost", "5559")


async def hello(request):
    msg = await zero_client.call_async("hello_world", "")
    print(msg)
    return web.Response(text=msg)


async def order(request):
    msg = await zero_client.call_async("save_order", {"user_id": "1", "items": ['apple', 'python']})
    print(msg)
    return web.json_response(msg)


async def gateway_app():
    app = web.Application()
    app.router.add_get('/', order)
    app.router.add_get('/hello', hello)
    return app
