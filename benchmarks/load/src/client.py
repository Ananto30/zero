import random
import time
import tracemalloc
from multiprocessing import Process

from zero import ZeroClient

zero_client = ZeroClient("localhost", 5555)


def verify_add():
    x = random.randint(0, 100)
    y = random.randint(0, 100)
    if zero_client.call("add", (x, y)) != x + y:
        print(f"Assertion failed, {x} + {y} != {x + y}")


def simulate_load():
    while True:
        verify_add()
        # 30 requests per second
        time.sleep(1 / 30)


def load(parallel=4):
    processes = []
    for i in range(parallel):
        p = Process(target=simulate_load)
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
