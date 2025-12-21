import logging
from typing import Tuple

from msgspec import Struct
from src.store import get_user_by_username, get_user_by_username_and_password

from zero import ZeroServer
from zero.protocols.tcp import TCPServer

from .generated_client.auth_client import RpcClient as AuthClient
from .generated_client.auth_client import zero_client as auth_client

log = logging.getLogger("UserService")

auth_rpc = AuthClient(auth_client)

app = ZeroServer(port=6003, protocol=TCPServer)


class UserResp(Struct):
    id: int
    username: str


@app.register_rpc
async def login(msg: Tuple[str, str]) -> str:
    username, password = msg
    user = await get_user_by_username_and_password(username, password)
    if user:
        return await auth_rpc.get_jwt(username)
    raise ValueError("Invalid username or password")


@app.register_rpc
async def get_user(username: str) -> UserResp:
    user = await get_user_by_username(username)
    if user:
        return UserResp(**user)
    raise ValueError(f"User with username {username} not found")


if __name__ == "__main__":
    app.run(workers=2)
