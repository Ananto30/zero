import msgpack

from zero import ZeroClient, ZeroPublisher

zero_client = ZeroClient("localhost", "5559")
zero_pub = ZeroPublisher("localhost", "5558", use_async=True)


def hello_test():
    resp = zero_client.call("hello_world", "")


def pub_test():
    resp = zero_pub.publish("hello_world", [1, 2, 3, 4])


def socket_test():
    import socket

    HOST = '127.0.0.1'  # The server's hostname or IP address
    PORT = 65432  # The port used by the server

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))
    s.sendall(msgpack.packb('Hello, world'))
    data = s.recv(1024)


if __name__ == "__main__":
    import timeit

    num_runs = 10_000
    duration = timeit.Timer(pub_test).timeit(number=num_runs)
    avg_duration = duration / num_runs
    req_per_sec = num_runs / duration
    print(f'On average it took {avg_duration} seconds, total {duration}, rps {req_per_sec}')
