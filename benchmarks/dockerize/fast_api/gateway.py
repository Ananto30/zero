import logging
from typing import Optional

import ujson
from aiohttp import ClientSession, TCPConnector
from fastapi import FastAPI

logger = logging.getLogger(__name__)

try:
    import uvloop

    uvloop.install()
except ImportError:
    logger.warning("Cannot use uvloop")


app = FastAPI()

session: Optional[ClientSession] = None


@app.on_event("startup")
async def startup():
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


@app.on_event("shutdown")
async def shutdown():
    """Clean up session on app shutdown"""
    if session:
        await session.close()


@app.get("/hello")
async def hello():
    r = await session.get("http://server:8011/hello")
    resp = await r.json()
    return resp


@app.get("/order")
async def order():
    r = await session.post(
        "http://server:8011/order",
        json={"user_id": "1", "items": ["apple", "python"]},
    )
    resp = await r.json()
    return resp
