import logging
from typing import Tuple

from zero import AsyncZeroClient, ZeroServer

from src.store import get_user_by_username, get_user_by_username_and_password

log = logging.getLogger("UserService")

auth_rpc = AsyncZeroClient("auth", 6000)


async def login(msg: Tuple[str, str]) -> str:
    username, password = msg
    user = await get_user_by_username_and_password(username, password)
    if user:
        jwt = await auth_rpc.call("get_jwt", username)
        return jwt
    else:
        return {"error": "Wrong credentials"}


async def get_user(username: str) -> dict:
    user = await get_user_by_username(username)
    if user:
        return user
    else:
        return {"error": "User not found"}


if __name__ == "__main__":
    app = ZeroServer(port=6001)
    app.register_rpc(login)
    app.register_rpc(get_user)
    app.run()
