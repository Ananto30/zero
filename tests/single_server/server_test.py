from tests.utils import kill_process, start_server
from zero import ZeroClient, ZeroServer
from zero.util import get_next_available_port


async def echo(msg: str) -> str:
    return msg


def server1_run(port):
    app = ZeroServer(port=port)
    app.register_rpc(echo)
    app.run(2)


def server2_run(port):
    app = ZeroServer(port=port)
    app.register_rpc(echo)
    app.run(2)


def test_two_servers_can_be_run():
    server1_port = get_next_available_port(4321)
    server2_port = get_next_available_port(server1_port + 1)

    p = start_server(server1_port, server1_run)
    assert get_next_available_port(server1_port) == server2_port
    p2 = start_server(server2_port, server2_run)

    c1 = ZeroClient("localhost", server1_port)
    c2 = ZeroClient("localhost", server2_port)

    assert c1.call("echo", "hello1") == "hello1"
    assert c2.call("echo", "hello2") == "hello2"

    kill_process(p)
    kill_process(p2)
