if __name__ == '__main__':

    from zero import ZeroServer
    import time
    import sys
    import os
    import signal
    from zero.common import get_next_available_port

    from threading import Thread
    def selfkill():
        time.sleep(10)
        print("self terminate after 10 sec")
        os.kill(os.getpid(), signal.SIGTERM)
    t = Thread(target=selfkill,daemon=True)
    t.start()


    def selfexit():
        time.sleep(5)
        print("self exit after 5 sec")
        os.kill(os.getpid(), signal.CTRL_C_EVENT if sys.platform == 'win32' else signal.SIGINT)

    t2 = Thread(target=selfexit,daemon=True)
    t2.start()


    def simple_function(a: str) -> str:
        return a

    app = ZeroServer(port=get_next_available_port(5559))
    app.register_rpc(simple_function)
    app.run()