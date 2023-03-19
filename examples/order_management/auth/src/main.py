import jwt

from zero import ZeroServer

SECRET = "secret"
ALGORITHM = "HS256"


async def get_jwt(username: str) -> str:
    data = {"username": username}
    return jwt.encode(data, SECRET, algorithm=ALGORITHM)


async def verify_jwt(jwt_token: str) -> dict:
    try:
        data = jwt.decode(jwt_token, SECRET, algorithms=[ALGORITHM])
        return data
    except jwt.exceptions.InvalidSignatureError:
        return {"error": "Invalid token"}


if __name__ == "__main__":
    app = ZeroServer(port=6000)
    app.register_rpc(get_jwt)
    app.register_rpc(verify_jwt)
    app.run()
