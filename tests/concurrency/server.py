import asyncio
import time

from zero import ZeroServer

PORT = 5559
HOST = "localhost"


def sleep(msg: int) -> str:
    sec = msg / 1000
    print(f"sleeping for {sec} sec...")
    time.sleep(sec)
    return f"slept for {msg} msecs"


async def sleep_async(msg: int) -> str:
    sec = msg / 1000
    print(f"sleeping for {sec} sec...")
    await asyncio.sleep(sec)
    return f"slept for {msg} msecs"


if __name__ == "__main__":
    print("Starting server on port", PORT)
    app = ZeroServer(port=PORT)
    app.register_rpc(sleep)
    app.register_rpc(sleep_async)
    app.run(cores=4)
