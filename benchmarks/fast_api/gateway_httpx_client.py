import logging
from typing import Optional

import httpx
from fastapi import FastAPI

logger = logging.getLogger(__name__)

try:
    import uvloop

    uvloop.install()
except ImportError:
    logger.warn("Cannot use uvloop")
    pass

client: Optional[httpx.AsyncClient] = None

app = FastAPI()


@app.get("/hello")
async def root():
    global client
    if client is None:
        client = httpx.AsyncClient()

    r = await client.get("http://localhost:8011/hello")
    return r.json()


@app.get("/order")
async def root():
    global client
    if client is None:
        client = httpx.AsyncClient()

    r = await client.post(
        "http://localhost:8011/order",
        json={"user_id": "1", "items": ["apple", "python"]},
    )
    return r.json()
