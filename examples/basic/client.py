import asyncio

import jwt

from zero import AsyncZeroClient
from zero.error import ZeroException

from .schema import User

zero_client = AsyncZeroClient("localhost", 5559)


async def echo():
    resp = await zero_client.call("echo", "Hi there!")
    print(resp)


async def enc_dec_jwt():
    encoded_jwt = jwt.encode({"user_id": "a1b2c3"}, "secret", algorithm="HS256")
    resp = await zero_client.call("decode_jwt", encoded_jwt)
    print(resp)


async def sum_list():
    resp = await zero_client.call("sum_list", [13, 54, 7, 7867, 43, 6456, 343])
    print(resp)


async def necho():
    try:
        resp = await zero_client.call("necho", "Hi there!")
        print(resp)
    except ZeroException as e:
        print(e)


async def two_rets():
    resp = await zero_client.call("two_rets", "Hi there!")
    print(resp)


async def hello_user():
    resp = await zero_client.call(
        "hello_user",
        User(
            name="John",
            age=25,
            emails=["hello@hello.com"],
        ),
    )
    print(resp)


async def hello_users():
    resp = await zero_client.call(
        "hello_users",
        [
            User(
                name="John",
                age=25,
                emails=["hello@hello.com"],
            ),
            User(
                name="Jane",
                age=30,
                emails=["hello@hello.com"],
            ),
        ],
    )
    print(resp)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(echo())
    loop.run_until_complete(enc_dec_jwt())
    loop.run_until_complete(sum_list())
    loop.run_until_complete(necho())
    loop.run_until_complete(two_rets())
    loop.run_until_complete(hello_user())
    loop.run_until_complete(hello_users())
    loop.close()
