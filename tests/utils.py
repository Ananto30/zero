import multiprocessing
import socket
import subprocess  # nosec
import sys
import threading
import time
import typing
from multiprocessing import Process

# Set spawn method to avoid fork() warnings with asyncio
ctx = multiprocessing.get_context("spawn")


def start_server(port: int, runner: typing.Callable) -> Process:
    p = ctx.Process(target=runner, args=(port,))
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
    # Try both IPv4 and IPv6 loopback addresses because on Windows
    # "localhost" may resolve to ::1 (IPv6) while the server could be
    # listening on IPv4 only (0.0.0.0). Try IPv4 first, then IPv6.
    for host in ("127.0.0.1", "::1"):
        family = socket.AF_INET6 if ":" in host else socket.AF_INET
        sock = socket.socket(family, socket.SOCK_STREAM)
        try:
            sock.settimeout(0.5)
            sock.connect((host, port))
            return True
        except socket.error:
            continue
        finally:
            sock.close()
    return False


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
    # Stream subprocess stdout so we can detect a readiness message instead of
    # relying solely on a port ping timeout. This is more robust across OSes.
    p = subprocess.Popen(
        ["python", "-m", module],
        shell=False,  # nosec
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    # Determine port based on module name
    if "tcp_server" in module:
        port = 5560
    elif "threaded_server" in module:
        port = 7777
    else:
        port = 5559

    timeout = 5

    lines: list[str] = []

    def _reader() -> None:
        try:
            for line in p.stdout:
                lines.append(line)
        except Exception:
            # If reading fails for any reason, swallow the error; we'll rely on ping
            return

    t = threading.Thread(target=_reader, daemon=True)
    t.start()

    start = time.time()
    ready_markers = (
        f"Starting TCP server at tcp://0.0.0.0:{port}",
        "Starting TCP worker",
        f"Starting server on port {port}",
    )

    while time.time() - start < timeout:
        if p.poll() is not None:
            # Subprocess exited early — include captured output for diagnostics
            raise RuntimeError(
                f"Subprocess exited prematurely. Output:\n{''.join(lines)}"
            )

        # If we see a readiness marker in output, double-check the port is reachable
        output = "".join(lines)
        if any(marker in output for marker in ready_markers):
            if _ping(port):
                return p

        # fallback to direct ping
        if _ping(port):
            return p

        time.sleep(0.1)

    # Timeout — include output for debugging
    raise TimeoutError(f"Server did not start in time. Output:\n{''.join(lines)}")


def kill_subprocess(process: subprocess.Popen):
    pid = process.pid
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()
