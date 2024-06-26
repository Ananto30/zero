import asyncio
import random
import time
from concurrent.futures import ProcessPoolExecutor

from zero import AsyncZeroClient

async_client = AsyncZeroClient("localhost", 5559)


async def task(semaphore, items):
    async with semaphore:
        try:
            await async_client.call("sum_sync", items)
            # res = await async_client.call("sum_async", items)
            # print(res)
        except Exception as e:
            print(e)


async def process_tasks(items_chunk):
    conc = 8
    semaphore = asyncio.BoundedSemaphore(conc)
    tasks = [task(semaphore, items) for items in items_chunk]
    await asyncio.gather(*tasks)
    await async_client.close()


def run_chunk(items_chunk):
    asyncio.run(process_tasks(items_chunk))


if __name__ == "__main__":
    process_no = 8

    print("Preparing data...")

    sum_items = [[random.randint(50, 500) for _ in range(10)] for _ in range(100000)]

    # Split sum_items into chunks for each process
    chunk_size = len(sum_items) // process_no
    items_chunks = [sum_items[i : i + chunk_size] for i in range(0, len(sum_items), chunk_size)]

    print("Running...")

    start = time.time()

    with ProcessPoolExecutor(max_workers=process_no) as executor:
        executor.map(run_chunk, items_chunks)

    end = time.time()
    time_taken_ms = 1e3 * (end - start)

    print(f"total time taken: {time_taken_ms} ms")
    print(f"requests per second: {len(sum_items) / time_taken_ms * 1e3}")
