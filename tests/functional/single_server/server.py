import asyncio
import datetime
import decimal
import enum
import time
import typing
import uuid
from dataclasses import dataclass

import jwt
import msgspec

from zero import ZeroServer

PORT = 5559
HOST = "localhost"

app = ZeroServer(port=PORT)


# None input
async def hello_world() -> str:
    return "hello world"


# bool input
@app.register_rpc
def echo_bool(msg: bool) -> bool:
    return msg


# int input
@app.register_rpc
def echo_int(msg: int) -> int:
    return msg


# float input
@app.register_rpc
def echo_float(msg: float) -> float:
    return msg


# str input
@app.register_rpc
def echo_str(msg: str) -> str:
    return msg


# bytes input
@app.register_rpc
def echo_bytes(msg: bytes) -> bytes:
    return msg


# bytearray input
@app.register_rpc
def echo_bytearray(msg: bytearray) -> bytearray:
    return msg


# tuple input
@app.register_rpc
def echo_tuple(msg: typing.Tuple[int, str]) -> typing.Tuple[int, str]:
    return msg


# list input
@app.register_rpc
def echo_list(msg: typing.List[int]) -> typing.List[int]:
    return msg


# dict input
@app.register_rpc
def echo_dict(msg: typing.Dict[int, str]) -> typing.Dict[int, str]:
    return msg


# set input
@app.register_rpc
def echo_set(msg: typing.Set[int]) -> typing.Set[int]:
    return msg


# frozenset input
@app.register_rpc
def echo_frozenset(msg: typing.FrozenSet[int]) -> typing.FrozenSet[int]:
    return msg


# datetime input
@app.register_rpc
def echo_datetime(msg: datetime.datetime) -> datetime.datetime:
    return msg


# date input
@app.register_rpc
def echo_date(msg: datetime.date) -> datetime.date:
    return msg


# time input
@app.register_rpc
def echo_time(msg: datetime.time) -> datetime.time:
    return msg


# uuid input
@app.register_rpc
def echo_uuid(msg: uuid.UUID) -> uuid.UUID:
    return msg


# decimal input
@app.register_rpc
def echo_decimal(msg: decimal.Decimal) -> decimal.Decimal:
    return msg


# enum input
class Color(enum.Enum):
    RED = 1
    GREEN = 2
    BLUE = 3


@app.register_rpc
def echo_enum(msg: Color) -> Color:
    return msg


# enum int input
class ColorInt(enum.IntEnum):
    RED = 1
    GREEN = 2
    BLUE = 3


@app.register_rpc
def echo_enum_int(msg: ColorInt) -> ColorInt:
    return msg


# dataclass input
@dataclass
class Dataclass:
    name: str
    age: int


@app.register_rpc
def echo_dataclass(msg: Dataclass) -> Dataclass:
    return msg


# typing.Tuple input
@app.register_rpc
def echo_typing_tuple(msg: typing.Tuple[int, str]) -> typing.Tuple[int, str]:
    return msg


# typing.List input
@app.register_rpc
def echo_typing_list(msg: typing.List[int]) -> typing.List[int]:
    return msg


# typing.Dict input
@app.register_rpc
def echo_typing_dict(msg: typing.Dict[int, str]) -> typing.Dict[int, str]:
    return msg


# typing.Set input
@app.register_rpc
def echo_typing_set(msg: typing.Set[int]) -> typing.Set[int]:
    return msg


# typing.FrozenSet input
@app.register_rpc
def echo_typing_frozenset(msg: typing.FrozenSet[int]) -> typing.FrozenSet[int]:
    return msg


# typing.Union input
@app.register_rpc
def echo_typing_union(msg: typing.Union[int, str]) -> typing.Union[int, str]:
    return msg


# typing.Optional input
@app.register_rpc
def echo_typing_optional(msg: typing.Optional[int]) -> int:
    return msg or 0


# msgspec.Struct input
class Message(msgspec.Struct):
    msg: str
    start_time: datetime.datetime


@app.register_rpc
def echo_msgspec_struct(msg: Message) -> Message:
    return msg


async def echo(msg: str) -> str:
    return msg


async def decode_jwt(msg: str) -> str:
    encoded_jwt = jwt.encode(msg, "secret", algorithm="HS256")  # type: ignore
    decoded_jwt = jwt.decode(encoded_jwt, "secret", algorithms=["HS256"])
    return decoded_jwt  # type: ignore


def sum_list(msg: typing.List[int]) -> int:
    return sum(msg)


def divide(msg: typing.Tuple[int, int]) -> int:
    return int(msg[0] / msg[1])


@app.register_rpc
def sleep(msec: int) -> str:
    sec = msec / 1000
    print(f"sleeping for {sec} sec...")
    time.sleep(sec)
    return f"slept for {msec} msecs"


@app.register_rpc
async def sleep_async(msec: int) -> str:
    sec = msec / 1000
    print(f"sleeping for {sec} sec...")
    await asyncio.sleep(sec)
    return f"slept for {msec} msecs"


@app.register_rpc
def error(msg: str) -> str:
    raise RuntimeError(msg)


@app.register_rpc
def send_bytes(msg: bytes) -> bytes:
    return msg


def run(port):
    print("Starting server on port", port)
    app.register_rpc(echo)
    app.register_rpc(hello_world)
    app.register_rpc(decode_jwt)
    app.register_rpc(sum_list)
    app.register_rpc(divide)
    app.run(2)


if __name__ == "__main__":
    run(PORT)
