import asyncio

from zero import AsyncZeroClient, ZeroClient

client = ZeroClient("localhost", 5559)
async_client = AsyncZeroClient("localhost", 5559)

# Create a semaphore outside of the task function
semaphore = asyncio.BoundedSemaphore(32)


async def task(sleep_time, i):
    # Use the semaphore as an async context manager to limit concurrency
    async with semaphore:
        res = await async_client.call("sleep", sleep_time)
        assert res == f"slept for {sleep_time} msecs"
        print(res, i)


async def main():
    tasks = [task(200, i) for i in range(500)]
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())
