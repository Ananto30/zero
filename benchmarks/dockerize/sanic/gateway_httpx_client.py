import logging
from typing import Optional

import httpx
from sanic import Sanic
from sanic.response import json, text

logger = logging.getLogger(__name__)

try:
    import uvloop

    uvloop.install()
except ImportError:
    logger.warn("Cannot use uvloop")
    pass

client: Optional[httpx.AsyncClient] = None

app = Sanic("My Hello, world app")


@app.route("/hello")
async def test(request):
    global client
    if client is None:
        client = httpx.AsyncClient()

    r = await client.get("http://localhost:8011/hello")
    return text(r.text)


@app.route("/order")
async def test(request):
    global client
    if client is None:
        client = httpx.AsyncClient()

    r = await client.post(
        "http://localhost:8011/order",
        json={"user_id": "1", "items": ["apple", "python"]},
    )
    return json(r.json())


if __name__ == "__main__":
    app.run()
