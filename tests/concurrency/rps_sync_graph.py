import random
import time
from functools import partial
from multiprocessing.pool import Pool

import matplotlib.pyplot as plt

from zero import ZeroClient

client = ZeroClient("localhost", 5559)

sum_func = partial(client.call, "sum_sync")


def get_and_sum(msg):
    return sum_func(msg)


if __name__ == "__main__":

    def run_task(process_no):
        sum_items = [[random.randint(50, 500) for _ in range(10)] for _ in range(100000)]

        start = time.time()
        with Pool(process_no) as pool:
            pool.map_async(get_and_sum, sum_items)
            pool.close()
            pool.join()
        end = time.time()

        time_taken_ms = 1e3 * (end - start)
        requests_per_second = len(sum_items) / time_taken_ms * 1e3
        return requests_per_second

    process_numbers = range(2, 128, 2)  # From 4 to 128, stepping by 4
    results = [run_task(pn) for pn in process_numbers]

    plt.plot(process_numbers, results)
    plt.xlabel("Number of Processes")
    plt.ylabel("Requests per Second")
    plt.title("Performance by Number of Processes")
    plt.show()
