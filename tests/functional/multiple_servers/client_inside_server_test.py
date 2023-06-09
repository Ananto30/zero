import pytest

from tests import constants
from zero import AsyncZeroClient, ZeroClient


def test_client_inside_server(server1, server2):  # pylint: disable=unused-argument
    client = ZeroClient("localhost", constants.MULTIPLE_SERVERS_PORT2)
    assert client.call("echo", "Hello") == "Server1: Hello"
    assert client.call("hello", None) == "Hello from server1"
    assert client.call("async_echo", "Hello") == "Server1: Hello"
    assert client.call("async_hello", None) == "Hello from server1"


@pytest.mark.asyncio
async def test_client_inside_server_async(
    server1, server2
):  # pylint: disable=unused-argument
    async_client = AsyncZeroClient("localhost", constants.MULTIPLE_SERVERS_PORT2)
    assert await async_client.call("echo", "Hello") == "Server1: Hello"
    assert await async_client.call("hello", None) == "Hello from server1"
    assert await async_client.call("async_echo", "Hello") == "Server1: Hello"
    assert await async_client.call("async_hello", None) == "Hello from server1"
