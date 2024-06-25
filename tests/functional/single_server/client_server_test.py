import datetime

import pytest
import requests

import zero.error
from zero import AsyncZeroClient, ZeroClient
from zero.error import ValidationException

from . import server
from .server import Message


def test_hello_world():
    zero_client = ZeroClient(server.HOST, server.PORT)
    msg = zero_client.call("hello_world", "")
    assert msg == "hello world"


def test_necho():
    zero_client = ZeroClient(server.HOST, server.PORT)
    with pytest.raises(zero.error.MethodNotFoundException):
        msg = zero_client.call("necho", "hello")
        assert msg is None


def test_echo_wrong_port():
    zero_client = ZeroClient(server.HOST, 5558, default_timeout=100)
    with pytest.raises(zero.error.ConnectionException):
        msg = zero_client.call("echo", "hello")
        assert msg is None


def test_sum_list():
    zero_client = ZeroClient(server.HOST, server.PORT)
    msg = zero_client.call("sum_list", [1, 2, 3])
    assert msg == 6


def test_echo_dict():
    zero_client = ZeroClient(server.HOST, server.PORT)
    msg = zero_client.call("echo_dict", {1: "b"})
    assert msg == {1: "b"}


def test_echo_dict_validation_error():
    zero_client = ZeroClient(server.HOST, server.PORT)
    with pytest.raises(ValidationException):
        msg = zero_client.call("echo_dict", {"a": "b"})
        assert msg == {
            "__zerror__validation_error": "Expected `int`, got `str` - at `key` in `$`"
        }


def test_echo_tuple():
    zero_client = ZeroClient(server.HOST, server.PORT)
    msg = zero_client.call("echo_tuple", (1, "a"))
    assert isinstance(msg, list)  # IMPORTANT
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
    with pytest.raises(zero.error.MethodNotFoundException):
        await zero_client.call("necho", "hello")


@pytest.mark.asyncio
async def test_echo_wrong_port_async():
    zero_client = AsyncZeroClient(server.HOST, 5558, default_timeout=100)
    with pytest.raises(zero.error.ConnectionException):
        msg = await zero_client.call("echo", "hello")
        assert msg is None


@pytest.mark.asyncio
async def test_echo_wrong_type_input_async():
    class Example:
        msg: str

    zero_client = AsyncZeroClient(server.HOST, server.PORT)
    with pytest.raises(TypeError):
        msg = await zero_client.call("echo", Example(msg="hello"))  # type: ignore
        assert msg is None


def test_msgspec_struct():
    now = datetime.datetime.now()
    zero_client = ZeroClient(server.HOST, server.PORT)
    msg = zero_client.call("msgspec_struct", now, return_type=Message)
    assert msg.msg == "hello world"
    assert msg.start_time == now


def test_send_bytes():
    zero_client = ZeroClient(server.HOST, server.PORT)
    msg = zero_client.call("send_bytes", b"hello")
    assert msg == b"hello"


def test_send_http_request():
    with pytest.raises(requests.exceptions.ReadTimeout):
        requests.get(f"http://{server.HOST}:{server.PORT}", timeout=2)


def test_server_works_after_multiple_http_requests():
    """Because of this issue https://github.com/Ananto30/zero/issues/41"""
    try:
        requests.get(f"http://{server.HOST}:{server.PORT}", timeout=2)
        requests.get(f"http://{server.HOST}:{server.PORT}", timeout=2)
        requests.get(f"http://{server.HOST}:{server.PORT}", timeout=2)
        requests.get(f"http://{server.HOST}:{server.PORT}", timeout=2)
        requests.get(f"http://{server.HOST}:{server.PORT}", timeout=2)
        requests.get(f"http://{server.HOST}:{server.PORT}", timeout=2)
    except requests.exceptions.ReadTimeout:
        pass
    zero_client = ZeroClient(server.HOST, server.PORT)
    msg = zero_client.call("hello_world", "")
    assert msg == "hello world"
