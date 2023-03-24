import time
from multiprocessing import Process

from tests.utils import kill_process, ping_until_success
from zero import ZeroServer
from zero.util import get_next_available_port

SERVER1_PORT = 4344
SERVER2_PORT = 4345


async def echo(msg: str) -> str:
    return msg


def server1():
    app = ZeroServer(port=SERVER1_PORT)
    app.register_rpc(echo)
    app.run()


def server2():
    app = ZeroServer(port=SERVER2_PORT)
    app.register_rpc(echo)
    app.run()


def test_two_servers_can_be_run():
    p = Process(target=server1)
    p.start()
    ping_until_success(SERVER1_PORT)

    assert get_next_available_port(SERVER1_PORT) == SERVER2_PORT

    p2 = Process(target=server2)
    p2.start()
    ping_until_success(SERVER2_PORT)

    kill_process(p)
    kill_process(p2)


def test_server_run():
    p = Process(target=server1)
    p.start()
    ping_until_success(SERVER1_PORT)
    kill_process(p)
