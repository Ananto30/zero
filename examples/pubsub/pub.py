import time

from zero import ZeroPublisher

zero_publisher = ZeroPublisher("localhost", 7878)


def publish_hi(n):
    zero_publisher.publish("hi", f"Hi there! {n}")


if __name__ == "__main__":
    counter = 1
    while True:
        publish_hi(counter)
        print(f"Published: {counter}")
        time.sleep(1)
        counter += 1
