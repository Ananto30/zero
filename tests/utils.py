import socket
import subprocess  # nosec
import time
import typing
from multiprocessing import Process

# process used in tests
process_map: dict[typing.Union[int, str], typing.Union[Process, subprocess.Popen]] = {}


def start_server(port: int, runner: typing.Callable) -> Process:
    p = Process(target=runner, args=(port,))
    p.start()
    _ping_until_success(port)
    process_map[port] = p
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
    process.kill()
    _wait_for_process_to_die(process)
    process.join()
    if pid and pid in process_map:
        del process_map[pid]


def _wait_for_process_to_die(process, timeout: int = 5):
    start = time.time()
    while time.time() - start < timeout:
        if not process.is_alive():
            return
        time.sleep(0.1)

    raise TimeoutError("Server did not die in time")


def start_subprocess(module: str) -> subprocess.Popen:
    p = subprocess.Popen(["python", "-m", module], shell=False)  # nosec
    _ping_until_success(5559)
    process_map[module] = p
    return p


def kill_subprocess(process: subprocess.Popen):
    pid = process.pid
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()
    if pid and pid in process_map:
        del process_map[pid]
