import jwt
from msgspec import Struct

from zero import ZeroServer
from zero.protocols.tcp import TCPServer

SECRET = "secret"
ALGORITHM = "HS256"

app = ZeroServer(port=6000, protocol=TCPServer)


class Traits(Struct):
    username: str


@app.register_rpc
async def get_jwt(username: str) -> str:
    data = {"username": username}
    return jwt.encode(data, SECRET, algorithm=ALGORITHM)


@app.register_rpc
async def verify_jwt(jwt_token: str) -> Traits:
    data = jwt.decode(jwt_token, SECRET, algorithms=[ALGORITHM])
    return Traits(**data)


if __name__ == "__main__":
    app.run(workers=2)
