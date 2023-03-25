import random
import time
from functools import partial
from multiprocessing import Pool

from zero import ZeroClient

client = ZeroClient("localhost", 5559)

func_sqrt = partial(client.call, "square_root")


def get_and_print(msg):
    resp = func_sqrt(msg)
    if resp != msg**0.5:
        print(f"expected: {msg ** 0.5}, got: {resp}")


if __name__ == "__main__":
    process_no = 32
    pool = Pool(process_no)

    args = []
    for _ in range(300000):
        args.append(random.randint(50, 500))

    start = time.time()

    res = pool.map_async(get_and_print, args)
    pool.close()
    pool.join()

    end = time.time()
    time_taken_ms = 1e3 * (end - start)

    print(f"total time taken: {time_taken_ms} ms")
    print(f"average time taken: {1e3 * time_taken_ms / len(args)} us")
    print(f"average time taken per process: {time_taken_ms / process_no} ms")
