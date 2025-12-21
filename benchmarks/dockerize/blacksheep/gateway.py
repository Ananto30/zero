import logging
from typing import Optional

from blacksheep import Application, JSONContent
from blacksheep import json as json_resp
from blacksheep import text
from blacksheep.client import ClientSession

logger = logging.getLogger(__name__)

try:
    import uvloop

    uvloop.install()
except ImportError:
    logger.warning("Cannot use uvloop")


session: Optional[ClientSession] = None

app = Application()
get = app.router.get


@app.on_start
async def startup(app):
    """Initialize session at app startup"""
    global session
    session = ClientSession()


@app.on_stop
async def shutdown(app):
    """Close session on shutdown"""
    if session:
        await session.close()


@get("/hello")
async def hello():
    resp = await session.get("http://server:8011/hello")
    txt = await resp.text()
    return text(txt)


@get("/order")
async def order():
    content = JSONContent(
        data={
            "user_id": "1",
            "items": ["apple", "python"],
        }
    )
    resp = await session.post("http://server:8011/order", content=content)
    return json_resp(await resp.json())
