import tracemalloc

from zero import ZeroServer

server = ZeroServer(port=5555)

arr = []


@server.register_rpc
def add(msg: tuple) -> int:
    x, y = msg

    # uncomment this to see the memory leak
    # arr.append(x)
    # print(sum(arr))

    return x + y


if __name__ == "__main__":
    tracemalloc.start()
    initial = tracemalloc.take_snapshot()

    try:
        server.run(workers=2)
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
