import asyncio
import random
import time
from contextlib import contextmanager

import pytest

import zero.error
from tests.single_server import server
from zero import AsyncZeroClient, ZeroClient


@pytest.mark.asyncio
async def test_concurrent_divide():
    async_client = AsyncZeroClient(server.HOST, server.PORT)

    req_resp = {
        (10, 2): 5,
        (10, 3): 3,
        (10, 4): 2,
        (10, 5): 2,
        (534, 2): 267,
        (534, 3): 178,
        (534, 4): 133,
        (534, 5): 106,
        (534, 6): 89,
        (534, 7): 76,
        (534, 8): 66,
        (534, 9): 59,
        (534, 10): 53,
        (534, 11): 48,
    }

    for req, resp in req_resp.items():
        assert await async_client.call("divide", req) == resp


def test_default_timeout():
    client = ZeroClient(server.HOST, server.PORT, default_timeout=100)
    with pytest.raises(zero.error.TimeoutException):
        msg = client.call("sleep", 200)
        assert msg is None

    msg = client.call("sleep", 1)
    assert msg == "slept for 1 msecs"


def test_local_timeout():
    client = ZeroClient(server.HOST, server.PORT)
    with pytest.raises(zero.error.TimeoutException):
        msg = client.call("sleep", 200, timeout=100)
        assert msg is None

    msg = client.call("sleep", 1, timeout=100)
    assert msg == "slept for 1 msecs"


def test_one_call_should_not_affect_another():
    client = ZeroClient(server.HOST, server.PORT)

    with pytest.raises(zero.error.TimeoutException):
        msg = client.call("sleep", 1000, timeout=10)
        assert msg is None

    msg = client.call("sleep", 1, timeout=100)
    assert msg == "slept for 1 msecs"

    msg = client.call("sleep", 1, timeout=100)
    assert msg == "slept for 1 msecs"

    with pytest.raises(zero.error.TimeoutException):
        msg = client.call("sleep", 100, timeout=10)
        assert msg is None

    msg = client.call("sleep", 1, timeout=100)
    assert msg == "slept for 1 msecs"


def test_random_timeout():
    client = ZeroClient(server.HOST, server.PORT)

    for _ in range(100):
        sleep_time = random.randint(10, 100)
        try:
            msg = client.call("sleep", sleep_time, timeout=50)
            assert msg == f"slept for {sleep_time} msecs"
        except zero.error.TimeoutException:
            assert sleep_time > 30  # considering network latency, 50 msecs is too low in github actions


def test_random_timeout_async():
    client = AsyncZeroClient(server.HOST, server.PORT)

    for _ in range(100):
        sleep_time = random.randint(10, 100)
        try:
            msg = asyncio.run(client.call("sleep", sleep_time, timeout=50))
            assert msg == f"slept for {sleep_time} msecs"
        except zero.error.ConnectionException:
            assert sleep_time > 30  # considering network latency, 50 msecs is too low in github actions


# TODO: fix this test
# @pytest.mark.asyncio
# async def test_async_sleep():
#     client = AsyncZeroClient(server.HOST, server.PORT)

#     async def task(sleep_time):
#         res = await client.call("sleep", sleep_time)
#         assert res == f"slept for {sleep_time} msecs"

#     start = time.time()
#     tasks = [task(200) for _ in range(5)]
#     await asyncio.gather(*tasks)
#     end = time.time()
#     time_taken_ms = 1e3 * (end - start)

#     assert time_taken_ms < 500
