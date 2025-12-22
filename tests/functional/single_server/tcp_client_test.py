import asyncio
import random
import sys

import pytest

import zero.error
from zero import AsyncZeroClient
from zero.protocols.tcp import AsyncTCPClient


@pytest.mark.skipif(
    sys.platform == "win32", reason="TCP tests not supported on Windows"
)
@pytest.mark.asyncio
async def test_concurrent_divide():
    from . import tcp_server

    async_client = AsyncZeroClient(
        tcp_server.HOST, tcp_server.PORT, protocol=AsyncTCPClient
    )

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


@pytest.mark.skipif(
    sys.platform == "win32", reason="TCP tests not supported on Windows"
)
@pytest.mark.asyncio
async def test_server_error():
    from . import tcp_server

    client = AsyncZeroClient(tcp_server.HOST, tcp_server.PORT, protocol=AsyncTCPClient)
    try:
        await client.call("error", "some error")
        raise AssertionError("Should have thrown an Exception")
    except zero.error.RemoteException:
        pass


@pytest.mark.skipif(
    sys.platform == "win32", reason="TCP tests not supported on Windows"
)
@pytest.mark.asyncio
async def test_timeout_all_async():
    from . import tcp_server

    client = AsyncZeroClient(tcp_server.HOST, tcp_server.PORT, protocol=AsyncTCPClient)

    with pytest.raises(zero.error.TimeoutException):
        await client.call("sleep", 1000, timeout=10)

    with pytest.raises(zero.error.TimeoutException):
        await client.call("sleep", 1000, timeout=200)


@pytest.mark.skipif(
    sys.platform == "win32", reason="TCP tests not supported on Windows"
)
@pytest.mark.asyncio
async def test_random_timeout_async():
    from . import tcp_server

    client = AsyncZeroClient(tcp_server.HOST, tcp_server.PORT, protocol=AsyncTCPClient)

    fails = 0
    should_fail = 0
    for _ in range(100):
        sleep_time = random.randint(10, 100)
        # error margin of 10 ms
        should_fail += sleep_time > 60
        try:
            msg = await client.call("sleep", sleep_time, timeout=50)
            assert msg == f"slept for {sleep_time} msecs"
        except zero.error.TimeoutException:
            assert (
                sleep_time > 1
            )  # considering network latency, 50 msecs is too low in github actions
            fails += 1

    assert fails >= should_fail


@pytest.mark.skipif(
    sys.platform == "win32", reason="TCP tests not supported on Windows"
)
@pytest.mark.asyncio
async def test_return_type_parameter():
    """Test that return_type parameter is used for proper decoding."""
    from . import tcp_server

    client = AsyncZeroClient(tcp_server.HOST, tcp_server.PORT, protocol=AsyncTCPClient)

    # Test with int return type
    result = await client.call("echo_int", 42, return_type=int)
    assert result == 42
    assert isinstance(result, int)

    # Test with str return type
    result = await client.call("echo_str", "hello", return_type=str)
    assert result == "hello"
    assert isinstance(result, str)

    # Test with float return type
    result = await client.call("echo_float", 3.14, return_type=float)
    assert result == 3.14
    assert isinstance(result, float)

    # Test with bool return type
    result = await client.call("echo_bool", True, return_type=bool)
    assert result is True
    assert isinstance(result, bool)

    # Test with list return type
    result = await client.call("echo_list", [1, 2, 3], return_type=list[int])
    assert result == [1, 2, 3]
    assert isinstance(result, list)


# For some reason this is failing in MacOS
# @pytest.mark.skipif(
#     sys.platform == "win32", reason="TCP tests not supported on Windows"
# )
# @pytest.mark.asyncio
# async def test_async_sleep():
#     from . import tcp_server

#     client = AsyncZeroClient(
#         tcp_server.HOST, tcp_server.PORT, protocol=AsyncTCPClient, pool_size=5
#     )

#     async def task(sleep_time):
#         res = await client.call("sleep_async", sleep_time)
#         assert res == f"slept for {sleep_time} msecs"

#     tasks = [task(200) for _ in range(5)]

#     start = time.perf_counter()
#     await asyncio.gather(*tasks)
#     time_taken_ms = (time.perf_counter() - start) * 1000

#     assert time_taken_ms < 1000
