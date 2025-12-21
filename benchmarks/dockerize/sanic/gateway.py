import logging
from typing import Optional

import ujson
from aiohttp import ClientSession, TCPConnector
from sanic import Sanic
from sanic.response import json, text

logger = logging.getLogger(__name__)

try:
    import uvloop

    uvloop.install()
except ImportError:
    logger.warning("Cannot use uvloop")


session: Optional[ClientSession] = None

app = Sanic("gateway")


@app.before_server_start
async def setup_session(app, loop):
    """Initialize session at app startup with optimized configuration"""
    global session
    connector = TCPConnector(
        limit=100,  # Total connections
        limit_per_host=30,  # Connections per host
        ttl_dns_cache=300,  # DNS cache TTL
        keepalive_timeout=30,  # Keep-alive timeout
    )

    session = ClientSession(
        connector=connector,
        json_serialize=ujson.dumps,  # Faster JSON serialization
        cookie_jar=None,  # Disable cookies for better performance
    )


@app.after_server_stop
async def cleanup_session(app, loop):
    """Clean up session on app shutdown"""
    if session:
        await session.close()


@app.route("/hello")
async def hello(request):
    r = await session.get("http://server:8011/hello")
    return text(await r.text())


@app.route("/order")
async def order(request):
    r = await session.post(
        "http://server:8011/order",
        json={"user_id": "1", "items": ["apple", "python"]},
    )
    return json(await r.json())


if __name__ == "__main__":
    app.run()
