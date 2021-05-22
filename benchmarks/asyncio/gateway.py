from aiohttp import ClientSession, web


async def hello(request):
    async with ClientSession() as session:
        resp = await session.post('http://localhost:8011/order', json={"user_id": "1", "items": ['apple', 'python']})
        return web.json_response(await resp.json())


async def gateway_app():
    app = web.Application()
    app.router.add_get('/', hello)
    return app
