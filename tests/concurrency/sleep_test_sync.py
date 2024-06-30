"""
This test ensures that the sync client can handle multiple requests concurrently.
And it doesn't mix up the responses.
"""

import random
import time
from functools import partial
from multiprocessing.pool import Pool

from zero import ZeroClient

client = ZeroClient("localhost", 5559)


func = partial(client.call, "sleep_async")


def get_and_print(msg):
    resp = func(msg)
    if resp != f"slept for {msg} msecs":
        print(f"expected: slept for {msg} msecs, got: {resp}")
    # print(resp)


if __name__ == "__main__":
    process_no = 32
    pool = Pool(process_no)

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
    print(f"average time taken per process: {time_taken_ms / process_no} ms")

    print(f"total time in args: {sum(sleep_times)} ms")
    print(f"average time in args: {sum(sleep_times) / len(sleep_times)} ms")
