import logging
import typing

import jwt

from zero import ZeroServer


async def echo(msg: str) -> str:
    return msg


async def hello_world() -> str:
    return "hello world"


async def decode_jwt(msg: str) -> dict:
    decoded_jwt = jwt.decode(msg, "secret", algorithms=["HS256"])
    logging.info(decoded_jwt)
    return decoded_jwt


async def sum_list(msg: typing.List[int]) -> int:
    return sum(msg)


async def two_rets(msg: typing.List) -> typing.Tuple[int, int]:
    return 1, 2


if __name__ == "__main__":
    app = ZeroServer(port=5559)
    app.register_rpc(echo)
    app.register_rpc(hello_world)
    app.register_rpc(decode_jwt)
    app.register_rpc(sum_list)
    app.register_rpc(two_rets)
    app.run()
