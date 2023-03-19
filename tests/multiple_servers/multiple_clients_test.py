import time
from multiprocessing.context import Process

import pytest
from server1 import run as run1
from server2 import run as run2

from tests.multiple_servers.config import Config
from tests.utils import ping_until_success
from zero import AsyncZeroClient, ZeroClient


@pytest.mark.asyncio
async def test_multiple_clients():
    try:
        from pytest_cov.embed import cleanup_on_sigterm
    except ImportError:
        pass
    else:
        cleanup_on_sigterm()

    server1_port = Config.SERVER1_PORT
    server2_port = Config.SERVER2_PORT

    p = Process(target=run1, args=(server1_port,))
    p.start()

    p2 = Process(target=run2, args=(server2_port,))
    p2.start()

    ping_until_success(server1_port)
    ping_until_success(server2_port)

    client1 = ZeroClient("localhost", server2_port)
    assert client1.call("echo", "Hello") == "Server1: Hello"
    assert client1.call("hello", None) == "Hello from server1"
    assert client1.call("async_echo", "Hello") == "Server1: Hello"
    assert client1.call("async_hello", None) == "Hello from server1"

    client2 = ZeroClient("localhost", server2_port)
    assert client2.call("echo", "Hello") == "Server1: Hello"
    assert client2.call("hello", None) == "Hello from server1"
    assert client2.call("async_echo", "Hello") == "Server1: Hello"
    assert client2.call("async_hello", None) == "Hello from server1"

    client3 = ZeroClient("localhost", server2_port)
    assert client3.call("echo", "Hello") == "Server1: Hello"
    assert client3.call("hello", None) == "Hello from server1"
    assert client3.call("async_echo", "Hello") == "Server1: Hello"
    assert client3.call("async_hello", None) == "Hello from server1"

    client4 = ZeroClient("localhost", server2_port)
    assert client4.call("echo", "Hello") == "Server1: Hello"
    assert client4.call("hello", None) == "Hello from server1"
    assert client4.call("async_echo", "Hello") == "Server1: Hello"
    assert client4.call("async_hello", None) == "Hello from server1"

    assert client3.call("async_echo", "Hello") == "Server1: Hello"
    assert client1.call("hello", None) == "Hello from server1"
    assert client4.call("async_hello", None) == "Hello from server1"
    assert client4.call("hello", None) == "Hello from server1"

    async_client1 = AsyncZeroClient("localhost", server2_port)
    assert await async_client1.call("echo", "Hello") == "Server1: Hello"
    assert await async_client1.call("hello", None) == "Hello from server1"
    assert await async_client1.call("async_echo", "Hello") == "Server1: Hello"
    assert await async_client1.call("async_hello", None) == "Hello from server1"

    async_client2 = AsyncZeroClient("localhost", server2_port)
    assert await async_client2.call("echo", "Hello") == "Server1: Hello"
    assert await async_client2.call("hello", None) == "Hello from server1"
    assert await async_client2.call("async_echo", "Hello") == "Server1: Hello"
    assert await async_client2.call("async_hello", None) == "Hello from server1"

    async_client3 = AsyncZeroClient("localhost", server2_port)
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
