import logging
from typing import Optional

import ujson
from aiohttp import ClientSession, TCPConnector, web

logger = logging.getLogger(__name__)

try:
    import uvloop

    uvloop.install()
except ImportError:
    logger.warning("Cannot use uvloop")

session: Optional[ClientSession] = None


async def init_session(app):
    """Initialize session at app startup"""
    global session
    connector = TCPConnector(
        limit=100,  # Total connections
        limit_per_host=30,  # Connections per host
        ttl_dns_cache=300,  # DNS cache TTL
        keepalive_timeout=30,  # Keep-alive timeout
    )
    session = ClientSession(
        connector=connector,
        json_serialize=ujson.dumps,  # Faster JSON
        cookie_jar=None,  # Disable cookies if not needed
    )
    app["session"] = session


async def cleanup_session(app):
    """Clean up session on shutdown"""
    await session.close()


async def hello(request):
    resp = await session.get("http://server:8011/hello")
    txt = await resp.text()
    return web.Response(text=txt)


async def order(request):
    resp = await session.post(
        "http://server:8011/order",
        json={"user_id": "1", "items": ["apple", "python"]},
    )
    return web.json_response(await resp.json())


app = web.Application()
app.on_startup.append(init_session)
app.on_cleanup.append(cleanup_session)
app.router.add_get("/order", order)
app.router.add_get("/hello", hello)
