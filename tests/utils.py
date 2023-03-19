def ping(port: int) -> bool:
    import socket

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect(("localhost", port))
        return True
    except socket.error:
        return False
    finally:
        s.close()


def ping_until_success(port: int, timeout: int = 5) -> bool:
    import time

    start = time.time()
    while time.time() - start < timeout:
        if ping(port):
            return True
        time.sleep(0.1)
    return False
