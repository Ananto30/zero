import asyncio
import datetime
import random
import sys
import time
import typing

import pytest

import zero.error
from zero import AsyncZeroClient
from zero.protocols.tcp import AsyncTCPClient


def get_async_client():
    from . import tcp_server

    return AsyncZeroClient(
        tcp_server.HOST,
        tcp_server.PORT,
        protocol=AsyncTCPClient,
        default_timeout=5000,  # github runners can be slow
        pool_size=5,
    )


@pytest.mark.skipif(
    sys.platform == "win32", reason="TCP tests not supported on Windows"
)
@pytest.mark.asyncio
async def test_concurrent_divide():
    client = get_async_client()

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
                assert await client.call("divide", req, timeout=500) == req_resp[req]
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
    client = get_async_client()

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
    client = get_async_client()

    with pytest.raises(zero.error.TimeoutException):
        await client.call("sleep", 1000, timeout=10)

    with pytest.raises(zero.error.TimeoutException):
        await client.call("sleep", 1000, timeout=200)


@pytest.mark.skipif(
    sys.platform == "win32", reason="TCP tests not supported on Windows"
)
@pytest.mark.asyncio
async def test_random_timeout_async():
    client = get_async_client()

    fails = 0
    should_fail = 0
    for _ in range(100):
        sleep_time = random.randint(10, 100)
        # considering network latency, adding an error margin of 15 ms
        should_fail += sleep_time > 65
        try:
            msg = await client.call("sleep", sleep_time, timeout=50)
            assert msg == f"slept for {sleep_time} msecs"
        except zero.error.TimeoutException:
            fails += 1

    assert fails >= should_fail


@pytest.mark.skipif(
    sys.platform == "win32", reason="TCP tests not supported on Windows"
)
@pytest.mark.asyncio
async def test_return_type_parameter():
    client = get_async_client()

    result = await client.call("echo_int", 42, return_type=int)
    assert result == 42
    assert isinstance(result, int)

    result = await client.call("echo_str", "hello", return_type=str)
    assert result == "hello"
    assert isinstance(result, str)

    result = await client.call("echo_float", 3.14, return_type=float)
    assert result == 3.14
    assert isinstance(result, float)

    result = await client.call("echo_bool", True, return_type=bool)
    assert result is True
    assert isinstance(result, bool)

    result = await client.call("echo_list", [1, 2, 3], return_type=list[int])
    assert result == [1, 2, 3]
    assert isinstance(result, list)


@pytest.mark.skipif(
    sys.platform == "win32", reason="TCP tests not supported on Windows"
)
@pytest.mark.asyncio
async def test_complex_return_types_union():
    client = get_async_client()

    result = await client.call(
        "echo_typing_union", 42, return_type=typing.Union[int, str]
    )
    assert result == 42
    assert isinstance(result, int)

    result = await client.call(
        "echo_typing_union", "hello", return_type=typing.Union[int, str]
    )
    assert result == "hello"
    assert isinstance(result, str)


@pytest.mark.skipif(
    sys.platform == "win32", reason="TCP tests not supported on Windows"
)
@pytest.mark.asyncio
async def test_complex_return_types_tuple():
    client = get_async_client()

    # Test Tuple[int, str]
    result = await client.call(
        "echo_typing_tuple", (42, "test"), return_type=typing.Tuple[int, str]
    )
    assert result == (42, "test") or result == [42, "test"]
    assert result[0] == 42
    assert result[1] == "test"

    # Test Tuple with different types
    result = await client.call(
        "echo_tuple", (100, "hello"), return_type=typing.Tuple[int, str]
    )
    assert result[0] == 100
    assert result[1] == "hello"


@pytest.mark.skipif(
    sys.platform == "win32", reason="TCP tests not supported on Windows"
)
@pytest.mark.asyncio
async def test_complex_return_types_nested_dict():
    client = get_async_client()

    # Test Dict[int, str] - basic dict
    result = await client.call(
        "echo_dict", {1: "one", 2: "two"}, return_type=typing.Dict[int, str]
    )
    assert result == {1: "one", 2: "two"}
    assert isinstance(result, dict)
    assert all(isinstance(k, int) for k in result.keys())
    assert all(isinstance(v, str) for v in result.values())


@pytest.mark.skipif(
    sys.platform == "win32", reason="TCP tests not supported on Windows"
)
@pytest.mark.asyncio
async def test_complex_return_types_pydantic():
    from . import tcp_server

    client = get_async_client()

    # Create a pydantic model instance
    model = tcp_server.PydanticModel(name="Alice", age=30)

    # Test Pydantic model return type
    result = await client.call(
        "echo_pydantic",
        {"name": "Alice", "age": 30},
        return_type=tcp_server.PydanticModel,
    )
    assert isinstance(result, tcp_server.PydanticModel)
    assert result.name == "Alice"
    assert result.age == 30


@pytest.mark.skipif(
    sys.platform == "win32", reason="TCP tests not supported on Windows"
)
@pytest.mark.asyncio
async def test_complex_return_types_msgspec_struct():
    from . import tcp_server

    client = get_async_client()

    # Create a message struct
    now = datetime.datetime.now()
    message_data = {"msg": "test message", "start_time": now}

    # Test msgspec Struct return type
    result = await client.call(
        "echo_msgspec_struct", message_data, return_type=tcp_server.Message
    )
    assert isinstance(result, tcp_server.Message)
    assert result.msg == "test message"
    assert result.start_time.year == now.year
    assert result.start_time.month == now.month
    assert result.start_time.day == now.day


@pytest.mark.skipif(
    sys.platform == "win32", reason="TCP tests not supported on Windows"
)
@pytest.mark.asyncio
async def test_complex_return_types_optional():
    client = get_async_client()

    # Test Optional[int] with value
    result = await client.call("echo_typing_optional", 42, return_type=int)
    assert result == 42
    assert isinstance(result, int)

    # Test Optional[int] with None (should return 0 per server implementation)
    result = await client.call("echo_typing_optional", None, return_type=int)
    assert result == 0
    assert isinstance(result, int)


@pytest.mark.skipif(
    sys.platform == "win32", reason="TCP tests not supported on Windows"
)
@pytest.mark.asyncio
async def test_complex_return_types_dataclass():
    from . import tcp_server

    client = get_async_client()

    # Test dataclass return type
    result = await client.call(
        "echo_dataclass", {"name": "Bob", "age": 25}, return_type=tcp_server.Dataclass
    )
    assert isinstance(result, tcp_server.Dataclass)
    assert result.name == "Bob"
    assert result.age == 25


@pytest.mark.skipif(
    sys.platform == "win32", reason="TCP tests not supported on Windows"
)
@pytest.mark.asyncio
async def test_complex_return_types_enum():
    from . import tcp_server

    client = get_async_client()

    # Test enum return type
    result = await client.call(
        "echo_enum", tcp_server.Color.RED, return_type=tcp_server.Color
    )
    assert isinstance(result, tcp_server.Color)
    assert result == tcp_server.Color.RED
    assert result.value == 1

    # Test IntEnum return type
    result = await client.call(
        "echo_enum_int", tcp_server.ColorInt.GREEN, return_type=tcp_server.ColorInt
    )
    assert isinstance(result, tcp_server.ColorInt)
    assert result == tcp_server.ColorInt.GREEN
    assert result.value == 2


@pytest.mark.skipif(
    sys.platform == "win32", reason="TCP tests not supported on Windows"
)
@pytest.mark.asyncio
async def test_async_sleep():
    client = get_async_client()

    async def task(sleep_time):
        res = await client.call("sleep_async", sleep_time)
        assert res == f"slept for {sleep_time} msecs"

    tasks = [task(200) for _ in range(5)]

    start = time.perf_counter()
    await asyncio.gather(*tasks)
    time_taken_ms = (time.perf_counter() - start) * 1000

    assert time_taken_ms < 1000
