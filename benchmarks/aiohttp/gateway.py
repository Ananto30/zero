import logging
from typing import Optional

from aiohttp import ClientSession, web

logger = logging.getLogger(__name__)

try:
    import uvloop

    uvloop.install()
except ImportError:
    logger.warn("Cannot use uvloop")
    pass

session: Optional[ClientSession] = None


async def hello(request):
    global session
    if session is None:
        session = ClientSession()

    resp = await session.get("http://localhost:8011/hello")
    txt = await resp.text()
    return web.Response(text=txt)


async def order(request):
    global session
    if session is None:
        session = ClientSession()

    resp = await session.post(
        "http://localhost:8011/order",
        json={"user_id": "1", "items": ["apple", "python"]},
    )
    return web.json_response(await resp.json())


async def gateway_app():
    app = web.Application()
    app.router.add_get("/order", order)
    app.router.add_get("/hello", hello)
    return app
