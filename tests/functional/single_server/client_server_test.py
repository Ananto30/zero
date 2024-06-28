import datetime
import decimal
import typing
import uuid

import pytest
import requests

import zero.error
from zero import AsyncZeroClient, ZeroClient
from zero.error import ValidationException

from . import server
from .server import Message


@pytest.fixture
def zero_client():
    return ZeroClient(server.HOST, server.PORT)


# bool input
def test_echo_bool(zero_client):
    assert zero_client.call("echo_bool", True) is True


# int input
def test_echo_int(zero_client):
    assert zero_client.call("echo_int", 42) == 42


# float input
def test_echo_float(zero_client):
    assert zero_client.call("echo_float", 3.14) == 3.14


# str input
def test_echo_str(zero_client):
    assert zero_client.call("echo_str", "hello") == "hello"


# bytes input
def test_echo_bytes(zero_client):
    assert zero_client.call("echo_bytes", b"hello") == b"hello"


# bytearray input
def test_echo_bytearray(zero_client):
    assert zero_client.call("echo_bytearray", bytearray(b"hello")) == bytearray(
        b"hello"
    )


# tuple input
def test_echo_tuple(zero_client):
    assert zero_client.call("echo_tuple", (1, "a"), return_type=tuple) == (1, "a")


# list input
def test_echo_list(zero_client):
    assert zero_client.call("echo_list", [1, 2, 3]) == [1, 2, 3]


# dict input
def test_echo_dict(zero_client):
    assert zero_client.call("echo_dict", {1: "a"}) == {1: "a"}


# set input
def test_echo_set(zero_client):
    assert zero_client.call("echo_set", {1, 2, 3}, return_type=set) == {1, 2, 3}


# frozenset input
def test_echo_frozenset(zero_client):
    assert zero_client.call(
        "echo_frozenset", frozenset({1, 2, 3}), return_type=frozenset
    ) == frozenset({1, 2, 3})


# datetime input
def test_echo_datetime(zero_client):
    now = datetime.datetime.now()
    assert zero_client.call("echo_datetime", now, return_type=datetime.datetime) == now


# date input
def test_echo_date(zero_client):
    today = datetime.date.today()
    assert zero_client.call("echo_date", today, return_type=datetime.date) == today


# time input
def test_echo_time(zero_client):
    now = datetime.datetime.now().time()
    assert zero_client.call("echo_time", now, return_type=datetime.time) == now


# uuid input
def test_echo_uuid(zero_client):
    uid = uuid.uuid4()
    assert zero_client.call("echo_uuid", uid, return_type=uuid.UUID) == uid


# decimal input
def test_echo_decimal(zero_client):
    value = decimal.Decimal("10.1")
    assert zero_client.call("echo_decimal", value, return_type=decimal.Decimal) == value


# enum input
def test_echo_enum(zero_client):
    assert (
        zero_client.call("echo_enum", server.Color.RED, return_type=server.Color)
        == server.Color.RED
    )


# enum int input
def test_echo_enum_int(zero_client):
    assert (
        zero_client.call("echo_enum_int", server.ColorInt.GREEN)
        == server.ColorInt.GREEN
    )


# dataclass input
def test_echo_dataclass(zero_client):
    data = server.Dataclass(name="John", age=30)
    result = zero_client.call("echo_dataclass", data, return_type=server.Dataclass)
    assert result == data


# typing.Tuple input
def test_echo_typing_tuple(zero_client):
    assert zero_client.call(
        "echo_typing_tuple", (1, "a"), return_type=typing.Tuple
    ) == (1, "a")


# typing.List input
def test_echo_typing_list(zero_client):
    assert zero_client.call("echo_typing_list", [1, 2, 3]) == [1, 2, 3]


# typing.Dict input
def test_echo_typing_dict(zero_client):
    assert zero_client.call("echo_typing_dict", {1: "a"}, return_type=typing.Dict) == {
        1: "a"
    }


# typing.Set input
def test_echo_typing_set(zero_client):
    assert zero_client.call("echo_typing_set", {1, 2, 3}, return_type=typing.Set) == {
        1,
        2,
        3,
    }


# typing.FrozenSet input
def test_echo_typing_frozenset(zero_client):
    assert zero_client.call(
        "echo_typing_frozenset", frozenset({1, 2, 3}), return_type=typing.FrozenSet
    ) == frozenset({1, 2, 3})


# typing.Union input
def test_echo_typing_union(zero_client):
    assert (
        zero_client.call("echo_typing_union", 1, return_type=typing.Union[str, int])
        == 1
    )
    assert (
        zero_client.call("echo_typing_union", "a", return_type=typing.Union[str, int])
        == "a"
    )


# typing.Optional input
def test_echo_typing_optional(zero_client):
    assert zero_client.call("echo_typing_optional", None) == 0
    assert (
        zero_client.call("echo_typing_optional", 1, return_type=typing.Optional[int])
        == 1
    )


# msgspec.Struct input
def test_echo_msgspec_struct(zero_client):
    msg = server.Message(msg="hello world", start_time=datetime.datetime.now())
    result = zero_client.call("echo_msgspec_struct", msg, return_type=server.Message)
    assert result.msg == msg.msg
    assert result.start_time == msg.start_time


def test_hello_world(zero_client):
    msg = zero_client.call("hello_world", "")
    assert msg == "hello world"


def test_necho(zero_client):
    with pytest.raises(zero.error.MethodNotFoundException):
        msg = zero_client.call("necho", "hello")
        assert msg is None


def test_echo_wrong_port():
    zero_client = ZeroClient(server.HOST, 5558, default_timeout=100)
    with pytest.raises(zero.error.ConnectionException):
        msg = zero_client.call("echo", "hello")
        assert msg is None


def test_sum_list(zero_client):
    msg = zero_client.call("sum_list", [1, 2, 3])
    assert msg == 6


def test_echo_dict_validation_error(zero_client):
    with pytest.raises(ValidationException):
        msg = zero_client.call("echo_dict", {"a": "b"})
        assert msg == {
            "__zerror__validation_error": "Expected `int`, got `str` - at `key` in `$`"
        }


def test_echo_tuple_2(zero_client):
    msg = zero_client.call("echo_tuple", (1, "a"))
    assert isinstance(msg, list)  # IMPORTANT
    assert msg == [1, "a"]


def test_echo_union(zero_client):
    msg = zero_client.call("echo_typing_union", 1)
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
    msg = Message("hello world", datetime.datetime.now())
    zero_client = ZeroClient(server.HOST, server.PORT)
    msg = zero_client.call("echo_msgspec_struct", msg, return_type=Message)
    assert msg.msg == "hello world"
    assert msg.start_time == msg.start_time


def test_send_bytes():
    zero_client = ZeroClient(server.HOST, server.PORT)
    msg = zero_client.call("send_bytes", b"hello")
    assert msg == b"hello"


def test_send_http_request():
    with pytest.raises(requests.exceptions.ReadTimeout):
        requests.get(f"http://{server.HOST}:{server.PORT}", timeout=0.1)


def test_server_works_after_multiple_http_requests():
    """Because of this issue https://github.com/Ananto30/zero/issues/41"""
    try:
        requests.get(f"http://{server.HOST}:{server.PORT}", timeout=0.1)
        requests.get(f"http://{server.HOST}:{server.PORT}", timeout=0.1)
        requests.get(f"http://{server.HOST}:{server.PORT}", timeout=0.1)
        requests.get(f"http://{server.HOST}:{server.PORT}", timeout=0.1)
        requests.get(f"http://{server.HOST}:{server.PORT}", timeout=0.1)
        requests.get(f"http://{server.HOST}:{server.PORT}", timeout=0.1)
    except requests.exceptions.ReadTimeout:
        pass
    zero_client = ZeroClient(server.HOST, server.PORT)
    msg = zero_client.call("hello_world", "")
    assert msg == "hello world"
