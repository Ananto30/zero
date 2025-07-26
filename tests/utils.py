import socket
import subprocess  # nosec
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

    raise TimeoutError("Server did not start in time")


def _ping(port: int) -> bool:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect(("localhost", port))
        return True
    except socket.error:
        return False
    finally:
        sock.close()


def kill_process(process: Process):
    pid = process.pid
    process.terminate()
    # allow the process a moment to exit cleanly
    process.join(timeout=5)
    if process.is_alive():
        process.kill()
        _wait_for_process_to_die(process, timeout=5)
    process.join()


def _wait_for_process_to_die(process, timeout: float = 5.0):
    start = time.time()
    while time.time() - start < timeout:
        if not process.is_alive():
            process.join()
            return
        time.sleep(0.1)

    raise TimeoutError("Server did not die in time")


def start_subprocess(module: str) -> subprocess.Popen:
    p = subprocess.Popen(["python", "-m", module], shell=False)  # nosec
    _ping_until_success(5559)
    return p


def kill_subprocess(process: subprocess.Popen):
    pid = process.pid
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()
