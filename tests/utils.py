import subprocess
import time
import typing
from multiprocessing import Process


def start_server(port: int, runner: typing.Callable) -> Process:
    p = Process(target=runner, args=(port,))
    p.start()
    _ping_until_success(port)
    return p


def _ping_until_success(port: int, timeout: int = 5):
    start = time.time()
    while time.time() - start < timeout:
        if _ping(port):
            return
        time.sleep(0.1)

    raise Exception("Server did not start in time")


def _ping(port: int) -> bool:
    import socket

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect(("localhost", port))
        return True
    except socket.error:
        return False
    finally:
        s.close()


def kill_process(process: Process):
    process.terminate()
    _wait_for_process_to_die(process)
    process.join()


def _wait_for_process_to_die(process, timeout: int = 5):
    start = time.time()
    while time.time() - start < timeout:
        if not process.is_alive():
            return
        time.sleep(0.1)

    raise Exception("Server did not die in time")


def start_subprocess(module: str) -> subprocess.Popen:
    p = subprocess.Popen(["python", "-m", module], shell=False)
    _ping_until_success(5559)
    return p


def kill_subprocess(process: subprocess.Popen):
    process.terminate()
    process.wait()
