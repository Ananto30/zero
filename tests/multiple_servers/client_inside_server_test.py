import time
from multiprocessing.context import Process

import pytest
from zero import AsyncZeroClient, ZeroClient

from server1 import run as run1
from server2 import run as run2


@pytest.mark.asyncio
async def test_client_inside_server():
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

    client = ZeroClient("localhost", 7899)
    assert client.call("echo", "Hello") == "Server1: Hello"
    assert client.call("hello", None) == "Hello from server1"
    assert client.call("async_echo", "Hello") == "Server1: Hello"
    assert client.call("async_hello", None) == "Hello from server1"

    async_client = AsyncZeroClient("localhost", 7899)
    assert await async_client.call("echo", "Hello") == "Server1: Hello"
    assert await async_client.call("hello", None) == "Hello from server1"
    assert await async_client.call("async_echo", "Hello") == "Server1: Hello"
    assert await async_client.call("async_hello", None) == "Hello from server1"

    p.terminate()
    p2.terminate()
