import time

from zero import ZeroSubscriber

zero_subscriber = ZeroSubscriber("localhost", 7878)


def on_message(message):
    print(message)


def on_message2(message):
    print(f"2 {message}")

if __name__ == "__main__":
    zero_subscriber.register_listener("hi", on_message)
    zero_subscriber.register_listener("hi", on_message2)
