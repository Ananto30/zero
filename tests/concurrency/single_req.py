from zero import ZeroClient

client = ZeroClient("localhost", 5559)

if __name__ == "__main__":
    for i in range(10):
        res = client.call("sleep", 100)
        if res != "slept for 100 msecs":
            print(f"expected: slept for 100 msecs, got: {res}")
        print(res)
