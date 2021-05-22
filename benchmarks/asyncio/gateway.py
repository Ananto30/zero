import uuid

import jwt
from aiohttp import ClientSession, web

from app.serializers import (CreateOrder, CreateOrderReq, Etype,
                             GetToken, GetTokenReq)


async def hello(request):
    # unpacked = auth_server_call(auth_socket)

    unpacked = order_server_call(order_socket)

    # unpacked = await async_server_call()

    # redis_calls()
    # unpacked = Yo("haha")

    return web.Response(text=str(vars(unpacked)))


# @exec_time
def auth_server_call(socket):
    rpc = GetToken(GetTokenReq("a1b2c3", "secret"))
    socket.send(rpc.pack())
    unpacked = Etype.unpack(socket.recv())
    # token = unpacked.response['token']
    # rpc = Authenticate(Token(token))
    # socket.send(rpc.pack())
    # unpacked = Etype.unpack(socket.recv())

    # print(vars(unpacked))
    # socket.close()
    return unpacked


# @exec_time
def order_server_call(socket):
    rpc = CreateOrder(CreateOrderReq('1', ['apple', 'python']))
    socket.send(rpc.pack())
    unpacked = Etype.unpack(socket.recv())
    # print(vars(unpacked))
    # socket.close()
    return unpacked


async def async_server_call():
    async with ClientSession() as session:
        async with session.get('http://localhost:8001/') as resp:
            pass
            # print(resp.status)
            # print(await resp.text())

    encoded_jwt = jwt.encode({'user_id': 'a1b2c3'}, 'secret', algorithm='HS256')
    decoded_jwt = jwt.decode(encoded_jwt, 'secret', algorithms=['HS256'])
    unpacked = Yo(decoded_jwt)
    return unpacked


def redis_calls():
    r = RedisClient()
    id = str(uuid.uuid4())
    r.set(id, "mama kemon asos")
    r.get(id)


async def my_web_app():
    app = web.Application()
    app.router.add_get('/', hello)
    return app
