import asyncio

import jwt

from zero import AsyncZeroClient
from zero.error import ZeroException

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


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(echo())
    loop.run_until_complete(enc_dec_jwt())
    loop.run_until_complete(sum_list())
    loop.run_until_complete(necho())
    loop.run_until_complete(two_rets())
