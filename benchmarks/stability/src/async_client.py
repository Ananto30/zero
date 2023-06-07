import asyncio
import random
import tracemalloc
from multiprocessing import Process

from zero import AsyncZeroClient

zero_client = AsyncZeroClient("localhost", 5555)


async def verify_add():
    x = random.randint(0, 100)
    y = random.randint(0, 100)
    res = await zero_client.call("add", (x, y))
    if res != x + y:
        print(f"Assertion failed, {x} + {y} != {x + y}")


async def task(semaphore):
    async with semaphore:
        await verify_add()


async def simulate_load(semaphore):
    while True:
        tasks = [task(semaphore) for _ in range(10)]
        await asyncio.gather(*tasks)
        # 30 requests per second
        await asyncio.sleep(1 / 3)


def sync_simulate_load():
    semaphore = asyncio.BoundedSemaphore(4)
    asyncio.run(simulate_load(semaphore))


def load(parallel=4):
    processes = []
    for i in range(parallel):
        p = Process(target=sync_simulate_load)
        p.start()
        processes.append(p)
    for p in processes:
        p.join()


if __name__ == "__main__":
    tracemalloc.start(10)
    initial = tracemalloc.take_snapshot()

    try:
        load()
    except KeyboardInterrupt:
        pass
    finally:
        snapshot = tracemalloc.take_snapshot()
        top_stats = snapshot.compare_to(initial, "lineno")
        top_stats = [stat for stat in top_stats if stat.size_diff > 0]
        print("[ Top 10 differences ]")
        for stat in top_stats[:10]:
            print(stat)
        tracemalloc.stop()
