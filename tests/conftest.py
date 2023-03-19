import time
import typing
from multiprocessing import Process

import jwt
import pytest

from tests.utils import ping_until_success
from zero import ZeroServer

DEFAULT_PORT = 5559


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
    app = ZeroServer(port=DEFAULT_PORT)
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
    try:
        from pytest_cov.embed import cleanup_on_sigterm
    except ImportError:
        pass
    else:
        cleanup_on_sigterm()

    p = Process(target=server)
    p.start()
    ping_until_success(DEFAULT_PORT)
    yield
    # p.kill()
    p.terminate()
