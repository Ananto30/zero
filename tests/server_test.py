import time
from multiprocessing import Process

from zero import ZeroServer
from zero.common import get_next_available_port

import signal
import os
import sys

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
        p = Process(target=server1)
        p.start()
        time.sleep(1)

        assert get_next_available_port(4344) == 4345

        p2 = Process(target=server2)
        p2.start()
        time.sleep(1)

        if p.exitcode is not None and p.exitcode!=0:
            raise Exception("p exit code !=0 p.exitcode="+str(p.exitcode))
        if p2.exitcode is not None and p2.exitcode!=0:
            raise Exception("p2 exit code !=0 p.exitcode="+str(p2.exitcode))
    finally:
        os.kill(p.pid ,signal.CTRL_C_EVENT if sys.platform == 'win32' else signal.SIGINT)
        os.kill(p2.pid,signal.CTRL_C_EVENT if sys.platform == 'win32' else signal.SIGINT)
        os.waitpid(p.pid ,0)
        os.waitpid(p2.pid,0)
    # raise Exception() # uncomment to see output




def test_server_run():

    p = Process(target=server1)
    p.start()
    time.sleep(5) # 1 sec is too short nothing starts until 2 seconds
    os.kill(p.pid,signal.CTRL_C_EVENT if sys.platform == 'win32' else signal.SIGINT)
    os.waitpid(p.pid ,0)
    # raise Exception() # uncomment see output