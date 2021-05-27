import logging
import typing

import jwt

from zero import ZeroServer


async def echo(msg):
    return msg


async def hello_world(msg):
    return "hello world"


async def decode_jwt(msg):
    decoded_jwt = jwt.decode(msg, 'secret', algorithms=['HS256'])
    logging.info(decoded_jwt)
    return decoded_jwt


async def sum_list(msg: typing.List):
    return sum(msg)


if __name__ == "__main__":
    app = ZeroServer(port=5559)
    app.register_rpc(echo)
    app.register_rpc(hello_world)
    app.register_rpc(decode_jwt)
    app.register_rpc(sum_list)
    app.run()
