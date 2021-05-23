import asyncio

from zero import ZeroClient

zero_client = ZeroClient("localhost", "5559")


async def hello_test():
    resp = zero_client.call("hello_world", "")
    print(resp)


if __name__ == "__main__":
    asyncio.run(hello_test())
