import asyncio
import random
import time

import pytest

import zero.error
from tests.functional.single_server import threaded_server
from zero import AsyncZeroClient, ZeroClient

from . import server


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

    total_pass = 0

    async def divide(semaphore, req):
        async with semaphore:
            try:
                assert (
                    await async_client.call("divide", req, timeout=500) == req_resp[req]
                )
                nonlocal total_pass
                total_pass += 1
            except zero.error.TimeoutException:
                pass

    semaphore = asyncio.BoundedSemaphore(4)

    tasks = [divide(semaphore, req) for req in req_resp]
    await asyncio.gather(*tasks)

    assert total_pass > 2


def test_server_error():
    client = ZeroClient(server.HOST, server.PORT)
    try:
        client.call("error", "some error")
        raise AssertionError("Should have thrown an Exception")
    except zero.error.RemoteException:
        pass


def test_multiple_errors():
    client = ZeroClient(server.HOST, server.PORT)
    with pytest.raises(zero.error.RemoteException):
        msg = client.call("error", "some error")
        assert msg is None
        msg = client.call("error", "some error")
        assert msg is None
        msg = client.call("error", "some error")
        assert msg is None
        msg = client.call("error", "some error")
        assert msg is None
        msg = client.call("error", "some error")
        assert msg is None

    msg = client.call("divide", (10, 2))
    assert msg == 5


def test_default_timeout():
    client = ZeroClient(server.HOST, server.PORT, default_timeout=100)
    with pytest.raises(zero.error.TimeoutException):
        msg = client.call("sleep", 200)
        assert msg is None

    msg = client.call("sleep", 1)
    assert msg == "slept for 1 msecs"

    client.close()


def test_local_timeout():
    client = ZeroClient(server.HOST, server.PORT)
    with pytest.raises(zero.error.TimeoutException):
        msg = client.call("sleep", 200, timeout=100)
        assert msg is None

    msg = client.call("sleep", 1, timeout=100)
    assert msg == "slept for 1 msecs"


def test_timeout_all():
    client = ZeroClient(server.HOST, server.PORT)
    with pytest.raises(zero.error.TimeoutException):
        msg = client.call("sleep", 1000, timeout=10)
        assert msg is None

    with pytest.raises(zero.error.TimeoutException):
        msg = client.call("sleep", 1000, timeout=200)
        assert msg is None

    # the server is 2 cores, so even if the timeout is greater,
    # server couldn't complete the last 2 calls and will timeout
    with pytest.raises(zero.error.TimeoutException):
        msg = client.call("sleep", 50, timeout=300)
        assert msg is None


def test_timeout_all_async():
    client = AsyncZeroClient(server.HOST, server.PORT)

    with pytest.raises(zero.error.TimeoutException):
        msg = asyncio.run(client.call("sleep", 1000, timeout=10))
        assert msg is None

    with pytest.raises(zero.error.TimeoutException):
        msg = asyncio.run(client.call("sleep", 1000, timeout=200))
        assert msg is None

    # the server is 2 cores, so even if the timeout is greater,
    # server couldn't complete the last 2 calls and will timeout
    with pytest.raises(zero.error.TimeoutException):
        msg = asyncio.run(client.call("sleep", 50, timeout=300))
        assert msg is None


# TODO fix server is blocked until a long running call is completed
# def test_one_call_should_not_affect_another():
#     client = ZeroClient(server.HOST, server.PORT)

#     sleep = partial(client.call, "sleep_async")

#     with pytest.raises(zero.error.TimeoutException):
#         msg = sleep(1000, timeout=100)
#         assert msg is None

#     msg = sleep(10, timeout=200)
#     assert msg == "slept for 10 msecs"

#     msg = sleep(10, timeout=200)
#     assert msg == "slept for 10 msecs"

#     with pytest.raises(zero.error.TimeoutException):
#         msg = sleep(200, timeout=100)
#         assert msg is None

#     msg = sleep(30, timeout=300)
#     assert msg == "slept for 30 msecs"


def test_random_timeout():
    client = ZeroClient(server.HOST, server.PORT)

    fails = 0
    should_fail = 0
    for _ in range(100):
        sleep_time = random.randint(10, 100)
        # error margin of 10 ms
        should_fail += sleep_time > 60
        try:
            msg = client.call("sleep", sleep_time, timeout=50)
            assert msg == f"slept for {sleep_time} msecs"
        except zero.error.TimeoutException:
            assert (
                sleep_time > 1
            )  # considering network latency, 50 msecs is too low in github actions
            fails += 1

    client.close()

    assert fails >= should_fail


def test_random_timeout_async():
    client = AsyncZeroClient(server.HOST, server.PORT)

    fails = 0
    should_fail = 0
    for _ in range(100):
        sleep_time = random.randint(10, 100)
        # error margin of 10 ms
        should_fail += sleep_time > 60
        try:
            msg = asyncio.run(client.call("sleep", sleep_time, timeout=50))
            assert msg == f"slept for {sleep_time} msecs"
        except zero.error.TimeoutException:
            assert (
                sleep_time > 1
            )  # considering network latency, 50 msecs is too low in github actions
            fails += 1

    client.close()

    assert fails >= should_fail


# @pytest.mark.asyncio
# async def test_async_sleep():
#     client = AsyncZeroClient(server.HOST, server.PORT)

#     async def task(sleep_time):
#         res = await client.call("sleep_async", sleep_time)
#         assert res == f"slept for {sleep_time} msecs"

#     tasks = [task(200) for _ in range(5)]

#     start = time.perf_counter()
#     await asyncio.gather(*tasks)
#     time_taken_ms = (time.perf_counter() - start) * 1000

#     assert time_taken_ms < 1000


def test_threaded_server_hello_world():
    client = ZeroClient(threaded_server.HOST, threaded_server.PORT)
    assert client.call("hello_world", "") == "hello world"
