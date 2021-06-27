import logging
from typing import Optional

import httpx
from aiohttp import ClientSession
from sanic import Sanic
from sanic.response import text, json

logger = logging.getLogger(__name__)

try:
    import uvloop

    uvloop.install()
except ImportError:
    logger.warn("Cannot use uvloop")
    pass

session: Optional[ClientSession] = None

app = Sanic("My Hello, world app")


@app.route("/hello")
async def test(request):
    global session
    if session is None:
        session = ClientSession()

    r = await session.get("http://localhost:8011/hello")
    return text(await r.text())


@app.route("/order")
async def test(request):
    global session
    if session is None:
        session = ClientSession()

    r = await session.post(
        "http://localhost:8011/order",
        json={"user_id": "1", "items": ["apple", "python"]},
    )
    return json(r.json())


if __name__ == "__main__":
    app.run()
