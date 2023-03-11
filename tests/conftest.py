import time
import typing
from multiprocessing import Process

import jwt
import pytest
from zero import ZeroServer


async def echo(msg: str) -> str:
    return msg


async def hello_world() -> str:
    return "hello world"


async def decode_jwt(msg: str) -> str:
    encoded_jwt = jwt.encode(msg, "secret", algorithm="HS256")
    decoded_jwt = jwt.decode(encoded_jwt, "secret", algorithms=["HS256"])
    return decoded_jwt


def sum_list(msg: typing.List[int]) -> int:
    return sum(msg)


def echo_dict(msg: typing.Dict[int, str]) -> typing.Dict[int, str]:
    return msg


def echo_tuple(msg: typing.Tuple[int, str]) -> typing.Tuple[int, str]:
    return msg


def echo_union(msg: typing.Union[int, str]) -> typing.Union[int, str]:
    return msg


def server():
    app = ZeroServer()
    app.register_rpc(echo)
    app.register_rpc(hello_world)
    app.register_rpc(decode_jwt)
    app.register_rpc(sum_list)
    app.register_rpc(echo_dict)
    app.register_rpc(echo_tuple)
    app.register_rpc(echo_union)
    app.run()


@pytest.fixture(autouse=True, scope="session")
def start_server():

    p = Process(target=server)
    p.start()
    time.sleep(1)
    yield
    # p.kill()
    p.terminate()
    # after session is finished clean up
    from pytest_cov.embed import cleanup
    cleanup()

