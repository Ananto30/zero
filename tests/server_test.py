from decimal import Decimal
import time
from multiprocessing import Process

from zero import ZeroServer
from zero.common import get_next_available_port

import signal
import os
import sys

from zero.client import  ZeroClient

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

    


def disabled_test_two_servers_can_be_run():
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




def disabled_test_server_run():

    p = Process(target=server1)
    p.start()
    time.sleep(5) # 1 sec is too short nothing starts until 2 seconds
    os.kill(p.pid,signal.CTRL_C_EVENT if sys.platform == 'win32' else signal.SIGINT)
    os.waitpid(p.pid ,0)
    # raise Exception() # uncomment see output



def server3():
    val={"a":"b"}
    async def get(msg:str) -> str:
       return val

    app = ZeroServer(port=4348, use_threads=True)
    # app = ZeroServer(port=4348, use_threads=False)
    app.register_rpc(get)
    app.run()

    print("exit1")
    

def client3():
    zero_client = ZeroClient("127.0.0.1", 4348, default_timeout=100)
    msg = zero_client.call("get",[""])
    print("got from server")
    print(msg)
    assert(msg)
    print("exit2")
    # assert msg is None
    
def test_threads_server_run():
    print("server3 starting")
    p = Process(target=server3)
    p.start()
    time.sleep(5)
    print("client3 starting")
    p2 = Process(target=client3)
    p2.start()

    time.sleep(5) # 1 sec is too short nothing starts until 2 seconds
    os.kill(p.pid,signal.CTRL_C_EVENT if sys.platform == 'win32' else signal.SIGINT)
    
    os.kill(p2.pid,signal.CTRL_C_EVENT if sys.platform == 'win32' else signal.SIGINT)
    # os.waitpid(p.pid ,0)
    # os.waitpid(p2.pid ,0)


    raise Exception() # uncomment see output

test_threads_server_run()