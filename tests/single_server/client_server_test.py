from dataclasses import dataclass

import pytest

from tests.single_server import server
from zero import AsyncZeroClient, ZeroClient
from zero.errors import MethodNotFoundException


def test_hello_world():
    zero_client = ZeroClient(server.HOST, server.PORT)
    msg = zero_client.call("hello_world", "")
    assert msg == "hello world"


def test_necho():
    zero_client = ZeroClient(server.HOST, server.PORT)
    with pytest.raises(MethodNotFoundException):
        msg = zero_client.call("necho", "hello")


def test_echo_wrong_port():
    zero_client = ZeroClient(server.HOST, 5558, default_timeout=100)
    msg = zero_client.call("echo", "hello")
    assert msg is None


def test_sum_list():
    zero_client = ZeroClient(server.HOST, server.PORT)
    msg = zero_client.call("sum_list", [1, 2, 3])
    assert msg == 6


def test_echo_dict():
    zero_client = ZeroClient(server.HOST, server.PORT)
    msg = zero_client.call("echo_dict", {"a": "b"})
    assert msg == {"a": "b"}


def test_echo_tuple():
    zero_client = ZeroClient(server.HOST, server.PORT)
    msg = zero_client.call("echo_tuple", (1, "a"))
    assert type(msg) == list  # IMPORTANT
    assert msg == [1, "a"]


def test_echo_union():
    zero_client = ZeroClient(server.HOST, server.PORT)
    msg = zero_client.call("echo_union", 1)
    assert msg == 1


@pytest.mark.asyncio
async def test_hello_world_async():
    zero_client = AsyncZeroClient(server.HOST, server.PORT)
    msg = await zero_client.call("hello_world", None)
    assert msg == "hello world"


@pytest.mark.asyncio
async def test_echo_async():
    zero_client = AsyncZeroClient(server.HOST, server.PORT)
    msg = await zero_client.call("echo", "hello")
    assert msg == "hello"


@pytest.mark.asyncio
async def test_necho_async():
    zero_client = AsyncZeroClient(server.HOST, server.PORT)
    with pytest.raises(MethodNotFoundException):
        msg = await zero_client.call("necho", "hello")


@pytest.mark.asyncio
async def test_echo_wrong_port_async():
    zero_client = AsyncZeroClient(server.HOST, 5558, default_timeout=100)
    msg = await zero_client.call("echo", "hello")
    assert msg is None


@pytest.mark.asyncio
async def test_echo_wrong_type_input_async():
    @dataclass
    class Example:
        msg: str

    zero_client = AsyncZeroClient(server.HOST, server.PORT)
    msg = await zero_client.call("echo", Example(msg="hello"))  # type: ignore
    assert msg is None
