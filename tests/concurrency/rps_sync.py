import random
import time
from functools import partial
from multiprocessing.pool import Pool

from zero import ZeroClient

client = ZeroClient("localhost", 5559)


sum_func = partial(client.call, "sum_sync")


def get_and_sum(msg):
    sum_func(msg)
    # resp = sum_func(msg)
    # print(resp)


if __name__ == "__main__":
    process_no = 8
    pool = Pool(process_no)

    sum_items = []
    for _ in range(100000):
        sum_items.append([random.randint(50, 500) for _ in range(10)])

    start = time.time()

    res = pool.map_async(get_and_sum, sum_items)
    pool.close()
    pool.join()

    end = time.time()
    time_taken_ms = 1e3 * (end - start)

    print(f"total time taken: {time_taken_ms} ms")
    print(f"requests per second: {len(sum_items) / time_taken_ms * 1e3}")
