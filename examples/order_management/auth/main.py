import jwt
from zero import ZeroServer

SECRET = "secret"
ALGORITHM = "HS256"


async def get_jwt(username: str) -> str:
    print("Creating JWT for user:", username)
    data = {"username": username}
    return jwt.encode(data, SECRET, algorithm=ALGORITHM)


async def verify_jwt(jwt_token: str) -> bool:
    try:
        jwt.decode(jwt_token, SECRET, algorithms=[ALGORITHM])
        return True
    except jwt.exceptions.InvalidSignatureError:
        return False


if __name__ == "__main__":
    app = ZeroServer(port=8100)
    app.register_rpc(get_jwt)
    app.register_rpc(verify_jwt)
    app.run()
