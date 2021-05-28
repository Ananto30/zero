import time
from multiprocessing import Process

import jwt
import pytest

from zero import ZeroServer, ZeroClient


async def echo(msg):
    return msg


async def hello_world(msg):
    return "hello world"


async def decode_jwt(msg):
    encoded_jwt = jwt.encode(msg, 'secret', algorithm='HS256')
    decoded_jwt = jwt.decode(encoded_jwt, 'secret', algorithms=['HS256'])
    return decoded_jwt


def test_hello_world():
    zero_client = ZeroClient("127.0.0.1", 5559, use_async=False)
    msg = zero_client.call("hello_world", "")
    assert (msg == "hello world")


@pytest.mark.asyncio
async def test_hello_world_async():
    zero_client = ZeroClient("127.0.0.1", 5559, use_async=True)
    msg = await zero_client.call_async("hello_world", "")
    assert (msg == "hello world")


@pytest.mark.asyncio
async def test_echo_async():
    zero_client = ZeroClient("127.0.0.1", 5559, use_async=True)
    msg = await zero_client.call_async("echo", "hello")
    assert (msg == "hello")


def server():
    app = ZeroServer()
    app.register_rpc(echo)
    app.register_rpc(hello_world)
    app.register_rpc(decode_jwt)
    app.run()


@pytest.fixture(autouse=True, scope="session")
def start_server():
    p = Process(target=server)
    p.start()
    time.sleep(1)
    yield
    # p.kill()
    p.terminate()
