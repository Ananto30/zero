import time
from multiprocessing import Process

from zero import ZeroServer
from zero.common import get_next_available_port


async def echo(msg: str) -> str:
    return msg


def server1():
    app = ZeroServer(port=4344)
    app.register_rpc(echo)
    app.run()


def server2():
    app = ZeroServer(port=4345)
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
    time.sleep(1)

    assert get_next_available_port(4344) == 4345

    p2 = Process(target=server2)
    p2.start()
    time.sleep(1)

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
    time.sleep(1)
    p.terminate()
