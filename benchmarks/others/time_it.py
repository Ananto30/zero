import asyncio
import socket
from functools import partial, wraps

import msgpack
import requests
from aiohttp import ClientSession

from zero import AsyncZeroClient, ZeroClient, ZeroPublisher

client = ZeroClient("localhost", 5559)
async_client = AsyncZeroClient("localhost", 5559)
zero_pub = ZeroPublisher("localhost", 5558, use_async=True)


def async_wrap(func):
    @wraps(func)
    async def run(*args, loop=None, executor=None, **kwargs):
        if loop is None:
            loop = asyncio.get_event_loop()
        pfunc = partial(func, *args, **kwargs)
        return await loop.run_in_executor(executor, pfunc)

    return run


async_call = async_wrap(client.call)


# WORST
def hello_test_requests():
    resp = requests.get("http://localhost:8000/hello")


async def hello_test_aiohttp():
    async with ClientSession() as session:
        resp = await session.get("http://localhost:8000/hello")


def hello_test():
    resp = client.call("hello_world", "")


async def hello_test_async():
    resp = await async_call("hello_world", "")


def echo_test():
    resp = client.call("echo", "hi")


async def echo_test_async():
    resp = await async_client.call_async("echo", "hi")


def pub_test():
    resp = zero_pub.publish("hello_world", [1, 2, 3, 4])


def socket_test():
    HOST = "127.0.0.1"  # The server's hostname or IP address
    PORT = 65430  # The port used by the server

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))

    s.sendall(msgpack.packb("Hello, world"))
    data = s.recv(1024)


def time_it(func):
    import timeit

    num_runs = 10_000
    duration = timeit.Timer(func).timeit(number=num_runs)
    print(
        f"{func.__name__} took {duration / num_runs} seconds, total {duration}, rps {num_runs / duration}"
    )


def run_async(func):
    def runner():
        loop = asyncio.get_event_loop()
        loop.run_until_complete(func())

    return runner


def async_hello():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(hello_test_async())


def async_hello_aiohttp():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(hello_test_aiohttp())


if __name__ == "__main__":
    # async_hello = run_async(hello_test_async)
    async_echo = run_async(echo_test_async)

    # pool = Pool(12)
    # t = partial(time_it, async_hello)
    # pool.starmap(t, [() for i in range(12)])
    # pool.close()
    # pool.join()
    time_it(async_hello)
    # time_it(hello_test)
    # time_it(echo_test)
    # time_it(async_echo)
