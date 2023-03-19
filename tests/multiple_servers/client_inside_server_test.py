import time
from multiprocessing.context import Process

import pytest
from server1 import run as run1
from server2 import run as run2

from tests.multiple_servers.config import Config
from tests.utils import ping_until_success
from zero import AsyncZeroClient, ZeroClient


@pytest.mark.asyncio
async def test_client_inside_server():
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

    client = ZeroClient("localhost", server2_port)
    assert client.call("echo", "Hello") == "Server1: Hello"
    assert client.call("hello", None) == "Hello from server1"
    assert client.call("async_echo", "Hello") == "Server1: Hello"
    assert client.call("async_hello", None) == "Hello from server1"

    async_client = AsyncZeroClient("localhost", server2_port)
    assert await async_client.call("echo", "Hello") == "Server1: Hello"
    assert await async_client.call("hello", None) == "Hello from server1"
    assert await async_client.call("async_echo", "Hello") == "Server1: Hello"
    assert await async_client.call("async_hello", None) == "Hello from server1"

    p.terminate()
    p2.terminate()
