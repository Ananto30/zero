import time
from multiprocessing.context import Process

import pytest
from zero import AsyncZeroClient, ZeroClient

import os
import signal
import sys

from server1 import run as run1
from server2 import run as run2


@pytest.mark.asyncio
async def test_client_inside_server():

    p = Process(target=run1)
    p.start()

    p2 = Process(target=run2)
    p2.start()

    time.sleep(2)

    try:
        client = ZeroClient("localhost", 7778)
        assert client.call("echo", "Hello") == "Server1: Hello"
        assert client.call("hello", None) == "Hello from server1"
        assert client.call("async_echo", "Hello") == "Server1: Hello"
        assert client.call("async_hello", None) == "Hello from server1"

        async_client = AsyncZeroClient("localhost", 7778)
        assert await async_client.call("echo", "Hello") == "Server1: Hello"
        assert await async_client.call("hello", None) == "Hello from server1"
        assert await async_client.call("async_echo", "Hello") == "Server1: Hello"
        assert await async_client.call("async_hello", None) == "Hello from server1"

    finally:
        os.kill(p.pid ,signal.CTRL_C_EVENT if sys.platform == 'win32' else signal.SIGINT)
        os.kill(p2.pid,signal.CTRL_C_EVENT if sys.platform == 'win32' else signal.SIGINT)
        os.waitpid(p.pid ,0)
        os.waitpid(p2.pid,0)
    # raise Exception() # uncomment to see output