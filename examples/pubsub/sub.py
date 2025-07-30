import threading
import time

from zero.pubsub.subscriber import Message, ZeroSubscriber

bytes_processed = 0
lock = threading.Lock()


def handle_message(msg: Message):
    """
    This function will be called for every message (replay + live).
    msg.payload is a bytes object.
    """
    # print(f"[{msg.topic}@{msg.offset} @ {msg.timestamp}] → {msg.payload!r}")
    # time.sleep(0.1)  # simulate processing time
    pass


def throughput_reporter():
    global bytes_processed
    while True:
        time.sleep(5)
        with lock:
            mbps = bytes_processed / 1_000_000 / 5
            print(f"Throughput: {mbps:.3f} MBps (last 5s)")
            bytes_processed = 0


def thread_safe_handle_message(msg: Message):
    global bytes_processed
    with lock:
        bytes_processed += len(msg.payload)
    handle_message(msg)


if __name__ == "__main__":
    consumer = ZeroSubscriber(
        broker_host="localhost",
        topic="orders",
        client_id="my-order-processor",
    )

    reporter_thread = threading.Thread(target=throughput_reporter, daemon=True)
    reporter_thread.start()

    consumer.register_func(thread_safe_handle_message, replay_mode="tracked")
