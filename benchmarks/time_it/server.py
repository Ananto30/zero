import time

from zero import ZeroServer

PORT = 5559
HOST = "localhost"


def square_root(msg: int) -> float:
    return msg**0.5


async def async_square_root(msg: int) -> float:
    return msg**0.5


def sleep(msg: int) -> str:
    sec = msg / 1000
    print(f"sleeping for {sec} sec...")
    time.sleep(sec)
    return f"slept for {msg} msecs"


def run(port):
    print("Starting server on port", port)
    app = ZeroServer(port=port)
    app.register_rpc(square_root)
    app.register_rpc(async_square_root)
    app.register_rpc(sleep)
    app.run(cores=4)


if __name__ == "__main__":
    run(PORT)
