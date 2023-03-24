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
    import socket

    def is_port_available(port: int) -> bool:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.bind(("localhost", port))
            return True
        except socket.error:
            return False
        finally:
            s.close()

    while not is_port_available(port):
        port += 1

    return port
