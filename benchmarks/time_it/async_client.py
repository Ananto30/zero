import asyncio
import random
import time

from zero import AsyncZeroClient

client = AsyncZeroClient("localhost", 5559)


async def get_and_print(semaphore, msg):
    async with semaphore:
        resp = await client.call("square_root", msg)
        if resp != msg**0.5:
            print(f"expected: {msg ** 0.5}, got: {resp}")
        # print(resp)


async def main():
    conc = 10
    semaphore = asyncio.BoundedSemaphore(conc)

    args = []
    for _ in range(300000):
        args.append(random.randint(50, 500))

    start = time.time()

    tasks = [get_and_print(semaphore, msg) for msg in args]
    await asyncio.gather(*tasks)

    end = time.time()
    time_taken_ms = 1e3 * (end - start)

    print(f"total time taken: {time_taken_ms} ms")
    print(f"average time taken: {1e3 * time_taken_ms / len(args)} us")
    print(f"average time taken per process: {time_taken_ms / conc} ms")


if __name__ == "__main__":
    asyncio.run(main())
