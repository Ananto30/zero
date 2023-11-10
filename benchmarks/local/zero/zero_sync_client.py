import time
from functools import partial
from multiprocessing.pool import Pool

from zero import ZeroClient

TOTAL_REQUESTS = 1_000_000

client = ZeroClient("localhost", 5559)

hello_world = partial(client.call, "hello_world", "")
save_order = partial(client.call, "save_order", {"user_id": "1", "items": ["apple", "python"]})


def success_call(func):
    try:
        func()
    except Exception:
        print("fail")


def rps(func, concurrency=10):
    pool = Pool(concurrency)
    start = time.time()
    divided = TOTAL_REQUESTS // concurrency
    for _ in range(concurrency):
        pool.map(success_call, [func] * divided)
    pool.close()
    pool.join()
    end = time.time()
    print(f"total time: {end - start}")
    print(f"total requests: {TOTAL_REQUESTS}")
    print(f"rps: {TOTAL_REQUESTS / (end - start)}")


if __name__ == "__main__":
    # rps(hello_world)
    rps(save_order)
