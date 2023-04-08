import pytest

from zero import AsyncZeroClient, ZeroClient

from .config import Config


@pytest.mark.asyncio
async def test_multiple_clients(server1, server2):  # pylint: disable=unused-argument
    server2_port = Config.SERVER2_PORT

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
