import asyncio
import random
import time
from contextlib import contextmanager

from zero.client import AsyncZeroClient


@contextmanager
def get_client():
    client = AsyncZeroClient("localhost", 5559)
    yield client
    client.close()


async_client = AsyncZeroClient("localhost", 5559)


async def task(semaphore, sleep_time):
    async with semaphore:
        res = await async_client.call("sleep", sleep_time)
        if res != f"slept for {sleep_time} msecs":
            print(f"expected: slept for {sleep_time} msecs, got: {res}")
        # print(res)


async def test():
    conc = 10
    semaphore = asyncio.BoundedSemaphore(conc)

    sleep_times = []
    for _ in range(1000):
        sleep_times.append(random.randint(50, 500))

    start = time.time()

    tasks = [task(semaphore, sleep_time) for sleep_time in sleep_times]
    await asyncio.gather(*tasks)

    end = time.time()
    time_taken_ms = 1e3 * (end - start)

    print(f"total time taken: {time_taken_ms} ms")
    print(f"average time taken: {time_taken_ms / len(tasks)} ms")
    print(f"average time taken per process: {time_taken_ms / conc} ms")

    print(f"total time in args: {sum(sleep_times)} ms")
    print(f"average time in args: {sum(sleep_times) / len(sleep_times)} ms")


if __name__ == "__main__":
    asyncio.run(test())
