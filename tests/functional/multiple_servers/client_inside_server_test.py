import pytest

from zero import AsyncZeroClient, ZeroClient

from .config import Config


def test_client_inside_server(server1, server2):
    client = ZeroClient("localhost", Config.SERVER2_PORT)
    assert client.call("echo", "Hello") == "Server1: Hello"
    assert client.call("hello", None) == "Hello from server1"
    assert client.call("async_echo", "Hello") == "Server1: Hello"
    assert client.call("async_hello", None) == "Hello from server1"


@pytest.mark.asyncio
async def test_client_inside_server_async(server1, server2):
    async_client = AsyncZeroClient("localhost", Config.SERVER2_PORT)
    assert await async_client.call("echo", "Hello") == "Server1: Hello"
    assert await async_client.call("hello", None) == "Hello from server1"
    assert await async_client.call("async_echo", "Hello") == "Server1: Hello"
    assert await async_client.call("async_hello", None) == "Hello from server1"
