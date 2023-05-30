import asyncio
import datetime
import time
import typing

import jwt
import msgspec

from zero import ZeroServer

PORT = 5559
HOST = "localhost"

app = ZeroServer(port=PORT)


async def echo(msg: str) -> str:
    return msg


async def hello_world() -> str:
    return "hello world"


async def decode_jwt(msg: str) -> str:
    encoded_jwt = jwt.encode(msg, "secret", algorithm="HS256")  # type: ignore
    decoded_jwt = jwt.decode(encoded_jwt, "secret", algorithms=["HS256"])
    return decoded_jwt  # type: ignore


def sum_list(msg: typing.List[int]) -> int:
    return sum(msg)


def echo_dict(msg: typing.Dict[int, str]) -> typing.Dict[int, str]:
    return msg


def echo_tuple(msg: typing.Tuple[int, str]) -> typing.Tuple[int, str]:
    return msg


def echo_union(msg: typing.Union[int, str]) -> typing.Union[int, str]:
    return msg


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


class Message(msgspec.Struct):
    msg: str
    start_time: datetime.datetime


@app.register_rpc
def msgspec_struct(start: datetime.datetime) -> Message:
    return Message(msg="hello world", start_time=start)


def run(port):
    print("Starting server on port", port)
    app.register_rpc(echo)
    app.register_rpc(hello_world)
    app.register_rpc(decode_jwt)
    app.register_rpc(sum_list)
    app.register_rpc(echo_dict)
    app.register_rpc(echo_tuple)
    app.register_rpc(echo_union)
    app.register_rpc(divide)
    app.run(2)


if __name__ == "__main__":
    run(PORT)
