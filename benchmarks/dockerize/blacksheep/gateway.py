import logging
from typing import Optional

from blacksheep import Application, JSONContent
from blacksheep import json as json_resp
from blacksheep import text
from blacksheep.client import ClientSession

app = Application()
get = app.router.get

logger = logging.getLogger(__name__)

try:
    import uvloop

    uvloop.install()
except ImportError:
    logger.warning("Cannot use uvloop")

session: Optional[ClientSession] = None


@get("/hello")
async def hello():
    global session
    if session is None:
        session = ClientSession()

    resp = await session.get("http://server:8011/hello")
    txt = await resp.text()
    return text(txt)


@get("/order")
async def order():
    global session
    if session is None:
        session = ClientSession()

    content = JSONContent(
        data={
            "user_id": "1",
            "items": ["apple", "python"],
        }
    )
    resp = await session.post("http://server:8011/order", content=content)
    return json_resp(await resp.json())
