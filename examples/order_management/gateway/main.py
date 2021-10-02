import logging
from typing import Optional

from aiohttp import ClientSession, web
from zero import AsyncZeroClient

logger = logging.getLogger(__name__)

auth_service = AsyncZeroClient("auth", 6000)
user_service = AsyncZeroClient("user", 6001)
order_service = AsyncZeroClient("order", 6002)


async def login(request):
    data = await request.json()
    username = data.get("username")
    password = data.get("password")
    jwt = await user_service.call("login", (username, password))
    return web.json_response({"jwt": jwt})


async def profile(request):
    jwt = request.headers.get("Authorization")
    auth = auth_service.verify_jwt(jwt)
    if not auth:
        return web.json_response({"error": "Invalid token"}, status=401)
    username = request.match_info["username"]
    user = user_service.get_user(username)
    return web.json_response(await user.json())


app = web.Application()
app.router.add_post("/login", login)
app.router.add_get("/profile", profile)
