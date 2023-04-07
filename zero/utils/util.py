import signal
import socket
import sys
import time
import uuid
from typing import Callable


def get_next_available_port(port: int) -> int:
    """
    Get the next available port.

    Parameters
    ----------
    port: int
        Port to start with.

    Returns
    -------
    int
        Next available port.

    """

    def is_port_available() -> bool:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.bind(("localhost", port))
            return True
        except socket.error:
            return False
        finally:
            sock.close()

    while not is_port_available():
        port += 1

    return port


def unique_id() -> str:
    """
    Generate a unique id.
    UUID without dashes.

    Returns
    -------
    str
        Unique id.

    """
    return str(uuid.uuid4()).replace("-", "")


def current_time_us() -> int:
    """
    Get current time in microseconds.

    Returns
    -------
    int
        Current time in microseconds.

    """
    return int(time.time() * 1e6)


def register_signal_term(sigterm_handler: Callable):
    """
    Register the signal term handler.

    Parameters
    ----------
    signal_term_handler: typing.Callable
        Signal term handler.

    """
    # this is important to catch KeyboardInterrupt
    original_sigint_handler = signal.signal(signal.SIGINT, signal.SIG_IGN)

    signal.signal(signal.SIGTERM, sigterm_handler)
    signal.signal(signal.SIGINT, original_sigint_handler)

    if sys.platform == "win32":
        signal.signal(signal.SIGBREAK, sigterm_handler)
    else:
        signal.signal(signal.SIGQUIT, sigterm_handler)
        signal.signal(signal.SIGHUP, sigterm_handler)
