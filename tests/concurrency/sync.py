import random
import time
from functools import partial
from multiprocessing.pool import Pool, ThreadPool

from zero.client import ZeroClient

client = ZeroClient("localhost", 5559)


func = partial(client.call, "sleep")


def get_and_print(msg):
    r = func(msg)
    print(r)


if __name__ == "__main__":
    pool = Pool(10)

    sleep_times = []
    for _ in range(1000):
        sleep_times.append(random.randint(50, 500))

    start = time.time()

    res = pool.map_async(get_and_print, sleep_times)
    pool.close()
    pool.join()

    end = time.time()
    time_taken_ms = 1e3 * (end - start)

    print(f"total time taken: {time_taken_ms} ms")
    print(f"average time taken: {time_taken_ms / len(sleep_times)} ms")
    print(f"average time taken per process: {time_taken_ms / 6} ms")

    print(f"total time in args: {sum(sleep_times)} ms")
    print(f"average time in args: {sum(sleep_times) / len(sleep_times)} ms")
