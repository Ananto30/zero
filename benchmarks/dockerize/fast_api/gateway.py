import logging
from typing import Optional

from aiohttp import ClientSession
from fastapi import FastAPI


logger = logging.getLogger(__name__)

try:
    import uvloop

    uvloop.install()
except ImportError:
    logger.warn("Cannot use uvloop")
    pass


app = FastAPI()

session: Optional[ClientSession] = None


@app.get("/hello")
async def root():
    global session
    if session is None:
        session = ClientSession()

    r = await session.get("http://server:8011/hello")
    resp = await r.json()
    return resp


@app.get("/order")
async def root():
    global session
    if session is None:
        session = ClientSession()

    r = await session.post(
        "http://server:8011/order",
        json={"user_id": "1", "items": ["apple", "python"]},
    )
    resp = await r.json()
    return resp
