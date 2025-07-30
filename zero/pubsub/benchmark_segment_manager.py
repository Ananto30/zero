import os
import random
import shutil
import string
import time

from zero.pubsub.segment_manager import SegmentManager


def random_payload(size: int) -> bytes:
    return "".join(
        random.choices(string.ascii_letters + string.digits, k=size)
    ).encode()


def benchmark(
    topic: str,
    num_msgs: int = 100_000,
    payload_size: int = 256,
    base_dir: str = "./tmp/log_bench",
):
    # clean slate
    if os.path.exists(base_dir):
        shutil.rmtree(base_dir)
    mgr = SegmentManager(base_dir)

    # --- Benchmark Appends ---
    # payloads = [random_payload(payload_size) for _ in range(num_msgs)]
    payload = random_payload(payload_size)
    start = time.perf_counter()
    for i in range(num_msgs):
        ts = int(time.time() * 1000)
        mgr.append(topic, payload, ts)
        # mgr.append(topic, payloads[i], ts)
    append_time = time.perf_counter() - start

    msgs_per_s = num_msgs / append_time
    mb_per_s = (num_msgs * payload_size) / append_time / (1024**2)
    print(
        f"APPEND: {msgs_per_s:,.0f} msgs/s, {mb_per_s:.1f} MB/s "
        f"({append_time:.2f}s for {num_msgs}x{payload_size}B)"
    )

    # --- Benchmark Reads ---
    start = time.perf_counter()
    records = mgr.read_from_offset(topic, 0)
    read_time = time.perf_counter() - start

    msgs_per_s = len(records) / read_time
    mb_per_s = (len(records) * payload_size) / read_time / (1024**2)
    print(
        f"READ:   {msgs_per_s:,.0f} msgs/s, {mb_per_s:.1f} MB/s "
        f"({read_time:.2f} s for {len(records)} records)"
    )


if __name__ == "__main__":
    print("256B payloads, 100K messages")
    benchmark(topic="bench:256B", num_msgs=100_000, payload_size=256)
    print("=" * 50)

    print("1KB payloads, 100K messages")
    benchmark(topic="bench:1KB", num_msgs=100_000, payload_size=1024)
    print("=" * 50)

    print("512KB payloads, 100K messages")
    benchmark(topic="bench:512KB", num_msgs=100_000, payload_size=512 * 1024)
    print("=" * 50)
