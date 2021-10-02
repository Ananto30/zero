import logging
from typing import Tuple

from zero import AsyncZeroClient, ZeroServer, ZeroClient

from store import get_user_by_username, get_user_by_username_and_password

log = logging.getLogger("UserService")

auth_rpc = None


async def login(msg: Tuple[str, str]) -> str:
    global auth_rpc
    if auth_rpc is None:
        auth_rpc = AsyncZeroClient("localhost", 8100)
        
    username, password = msg
    user = await get_user_by_username_and_password(username, password)
    if user:
        
        jwt = await auth_rpc.call("get_jwt", username)
        return jwt
    else:
        return {"error": "wrong credentials"}

    jwt = await auth_rpc.call("get_jwt", username)
    return jwt


async def get_user(username: str) -> dict:
    user = await get_user_by_username(username)
    if user:
        return user
    else:
        return {"error": "user not found"}


if __name__ == "__main__":
    app = ZeroServer(port=8101)
    app.register_rpc(login)
    app.register_rpc(get_user)
    app.run()
