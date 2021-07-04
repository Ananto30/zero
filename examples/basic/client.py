import asyncio

import jwt

from zero import ZeroClient

zero_client = ZeroClient("localhost", 5559)


async def echo():
    resp = await zero_client.call_async("echo", "Hi there!")
    print(resp)


async def enc_dec_jwt():
    encoded_jwt = jwt.encode({'user_id': 'a1b2c3'}, 'secret', algorithm='HS256')
    resp = await zero_client.call_async("decode_jwt", encoded_jwt)
    print(resp)


async def sum_list():
    resp = await zero_client.call_async("sum_list", [13, 54, 7, 7867, 43, 6456, 343])
    print(resp)


async def echo():
    resp = await zero_client.call_async("necho", "Hi there!")
    print(resp)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(echo())
    loop.run_until_complete(enc_dec_jwt())
    loop.run_until_complete(sum_list())
