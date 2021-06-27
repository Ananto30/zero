import logging
from typing import Optional

import httpx
from aiohttp import ClientSession
from fastapi import FastAPI

logger = logging.getLogger(__name__)

try:
    import uvloop

    uvloop.install()
except ImportError:
    logger.warn("Cannot use uvloop")
    pass

session: Optional[ClientSession] = None

app = FastAPI()


@app.get("/hello")
async def root():
    global session
    if session is None:
        session = ClientSession()

    r = await session.get("http://localhost:8011/hello")
    resp = await r.json()
    return resp


@app.get("/order")
async def root():
    global session
    if session is None:
        session = ClientSession()

    r = await session.post(
        "http://localhost:8011/order",
        json={"user_id": "1", "items": ["apple", "python"]},
    )
    resp = await r.json()
    return resp
