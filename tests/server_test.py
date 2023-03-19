import time
from multiprocessing import Process

from tests.utils import ping_until_success
from zero import ZeroServer
from zero.common import get_next_available_port

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
    try:
        from pytest_cov.embed import cleanup_on_sigterm
    except ImportError:
        pass
    else:
        cleanup_on_sigterm()

    p = Process(target=server1)
    p.start()
    ping_until_success(SERVER1_PORT)

    assert get_next_available_port(SERVER1_PORT) == SERVER2_PORT

    p2 = Process(target=server2)
    p2.start()
    ping_until_success(SERVER2_PORT)

    p.terminate()
    p2.terminate()


def test_server_run():
    try:
        from pytest_cov.embed import cleanup_on_sigterm
    except ImportError:
        pass
    else:
        cleanup_on_sigterm()

    p = Process(target=server1)
    p.start()
    ping_until_success(SERVER1_PORT)
    p.terminate()
