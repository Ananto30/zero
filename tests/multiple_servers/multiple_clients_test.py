import time
from multiprocessing.context import Process

import pytest
from server1 import run as run1
from server2 import run as run2

from zero import AsyncZeroClient, ZeroClient


@pytest.mark.asyncio
async def test_multiple_clients():
    try:
        from pytest_cov.embed import cleanup_on_sigterm
    except ImportError:
        pass
    else:
        cleanup_on_sigterm()

    p = Process(target=run1)
    p.start()

    p2 = Process(target=run2)
    p2.start()

    time.sleep(2)

    client1 = ZeroClient("localhost", 7778)
    assert client1.call("echo", "Hello") == "Server1: Hello"
    assert client1.call("hello", None) == "Hello from server1"
    assert client1.call("async_echo", "Hello") == "Server1: Hello"
    assert client1.call("async_hello", None) == "Hello from server1"

    client2 = ZeroClient("localhost", 7778)
    assert client2.call("echo", "Hello") == "Server1: Hello"
    assert client2.call("hello", None) == "Hello from server1"
    assert client2.call("async_echo", "Hello") == "Server1: Hello"
    assert client2.call("async_hello", None) == "Hello from server1"

    client3 = ZeroClient("localhost", 7778)
    assert client3.call("echo", "Hello") == "Server1: Hello"
    assert client3.call("hello", None) == "Hello from server1"
    assert client3.call("async_echo", "Hello") == "Server1: Hello"
    assert client3.call("async_hello", None) == "Hello from server1"

    client4 = ZeroClient("localhost", 7778)
    assert client4.call("echo", "Hello") == "Server1: Hello"
    assert client4.call("hello", None) == "Hello from server1"
    assert client4.call("async_echo", "Hello") == "Server1: Hello"
    assert client4.call("async_hello", None) == "Hello from server1"

    assert client3.call("async_echo", "Hello") == "Server1: Hello"
    assert client1.call("hello", None) == "Hello from server1"
    assert client4.call("async_hello", None) == "Hello from server1"
    assert client4.call("hello", None) == "Hello from server1"

    async_client1 = AsyncZeroClient("localhost", 7778)
    assert await async_client1.call("echo", "Hello") == "Server1: Hello"
    assert await async_client1.call("hello", None) == "Hello from server1"
    assert await async_client1.call("async_echo", "Hello") == "Server1: Hello"
    assert await async_client1.call("async_hello", None) == "Hello from server1"

    async_client2 = AsyncZeroClient("localhost", 7778)
    assert await async_client2.call("echo", "Hello") == "Server1: Hello"
    assert await async_client2.call("hello", None) == "Hello from server1"
    assert await async_client2.call("async_echo", "Hello") == "Server1: Hello"
    assert await async_client2.call("async_hello", None) == "Hello from server1"

    async_client3 = AsyncZeroClient("localhost", 7778)
    assert await async_client3.call("echo", "Hello") == "Server1: Hello"
    assert await async_client3.call("hello", None) == "Hello from server1"
    assert await async_client3.call("async_echo", "Hello") == "Server1: Hello"
    assert await async_client3.call("async_hello", None) == "Hello from server1"

    assert await async_client2.call("hello", None) == "Hello from server1"
    assert await async_client3.call("hello", None) == "Hello from server1"
    assert await async_client3.call("async_echo", "Hello") == "Server1: Hello"
    assert await async_client1.call("async_echo", "Hello") == "Server1: Hello"
    assert await async_client1.call("async_hello", None) == "Hello from server1"

    p.terminate()
    p2.terminate()
