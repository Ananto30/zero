import asyncio
import time

from zero import ZeroServer

app = ZeroServer(port=5559)


@app.register_rpc
def sleep(msg: int) -> str:
    sec = msg / 1000
    print(f"sleeping for {sec} sec...")
    time.sleep(sec)
    return f"slept for {msg} msecs"


@app.register_rpc
async def sleep_async(msg: int) -> str:
    sec = msg / 1000
    print(f"sleeping for {sec} sec...")
    await asyncio.sleep(sec)
    return f"slept for {msg} msecs"


if __name__ == "__main__":
    app.run(workers=8)
