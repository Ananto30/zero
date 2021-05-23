from aiohttp import ClientSession, web


async def order(request):
    async with ClientSession() as session:
        resp = await session.post('http://localhost:8011/order', json={"user_id": "1", "items": ['apple', 'python']})
        return web.json_response(await resp.json())


async def hello(request):
    async with ClientSession() as session:
        resp = await session.get('http://localhost:8011/hello')
        txt = await resp.text()
        return web.Response(text=txt)


async def gateway_app():
    app = web.Application()
    app.router.add_get('/', order)
    app.router.add_get('/hello', hello)
    return app
