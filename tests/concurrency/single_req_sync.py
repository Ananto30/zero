from zero import ZeroClient

client = ZeroClient("localhost", 5559)

if __name__ == "__main__":
    for i in range(50):
        res = client.call("sleep", 200)
        assert res == "slept for 200 msecs"
        print(res)
