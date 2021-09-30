<p align="center">
    <img height="300px" src="https://ananto30.github.io/i/1200xCL_TP.png" /> 
</p>
<p align="center">
    <em>Zero is a RPC framework to build fast and high performance Python microservices</em>
</p>
<p align="center">
    <a href="https://codecov.io/gh/Ananto30/zero" target="_blank">
        <img src="https://codecov.io/gh/Ananto30/zero/branch/main/graph/badge.svg?token=k0aA0G6NLs" />
    </a>
    <a href="https://pypi.org/project/zeroapi/" target="_blank">
        <img src="https://img.shields.io/pypi/v/zeroapi" />
    </a>
</p>
<hr>

Zero is actually a RPC like framework that passes message between client server like architecture. Also supports Pub-Sub.

**Features**:

- Zero provides **faster communication** (see [benchmarks](https://github.com/Ananto30/zero#benchmarks-)) between the microservices using [zeromq](https://zeromq.org/) under the hood.
- Zero uses messages for communication and traditional **client-server** or **request-reply** pattern is supported.
- Support for both **Async** and **sync**.
- The base server (ZeroServer) **utilizes all cpu cores**.
- **Code generation**! See [example](https://github.com/Ananto30/zero#code-generation-) 👇

**Philosophy** behind Zero:

- **Zero learning curve**: The learning curve is tends to zero. You just add your functions and spin up a server, literally that's it!
  The framework hides the complexity of messaging pattern that enables faster communication.
- **ZeroMQ**: An awesome messaging library enables the power of Zero.

Let's get started!

## Getting started 🚀

_Ensure Python 3.8+_

```
pip install zeroapi
```

- Create a `server.py`

```python
from zero import ZeroServer

def echo(msg: str) -> msg:
    return msg

async def hello_world() -> msg:
    return "hello world"


if __name__ == "__main__":
    app = ZeroServer(port=5559)
    app.register_rpc(echo)
    app.register_rpc(hello_world)
    app.run()

```

Please note that server **RPC methods are type hinted**. Type hint is **must** in Zero server.

_See the method type async or sync, doesn't matter._ 😃

- Run it

```
python -m server
```

- Call the rpc methods

```python
from zero import ZeroClient

zero_client = ZeroClient("localhost", 5559)

def echo():
    resp = zero_client.call("echo", "Hi there!")
    print(resp)

def hello():
    resp = zero_client.call("hello_world", None)
    print(resp)


if __name__ == "__main__":
    echo()
    hello()

```

Or using async client -

```python
import asyncio

from zero import ZeroClient

zero_client = ZeroClient("localhost", 5559, use_async=True)

async def echo():
    resp = await zero_client.call_async("echo", "Hi there!")
    print(resp)

async def hello():
    resp = await zero_client.call_async("hello_world", None)
    print(resp)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(echo())
    loop.run_until_complete(hello())

```

## Code Generation! 🙌

You can also use our code generation tool to generate Python client code!

After running the server, like above, you can call the server to get the client code.

```shell
python -m zero.generate_client --host localhost --port 5559 --overwrite-dir ./my_client
```

It will generate client like this -

```python
import typing  # remove this if not needed
from typing import List, Dict, Union, Optional, Tuple  # remove this if not needed
from zero import ZeroClient


zero_client = ZeroClient("localhost", 5559, use_async=False)


class RpcClient:
    def __init__(self, zero_client: ZeroClient):
        self._zero_client = zero_client

    def echo(self, msg: str) -> str:
        return self.zero_client.call("echo", msg)

    def hello_world(self, msg: str) -> str:
        return self.zero_client.call("hello_world", msg)

```

You can just use this -

```python
from my_client import RpcClient, zero_client

client = RpcClient(zero_client)

if __name__ == "__main__":
    client.echo("Hi there!")
    client.hello_world(None)
```

Using `zero.generate_client` you can generate client code for even remote servers using the `--host` and `--port` options. You don't need access to the code 😃

## Important notes 📝

- `ZeroServer` should always be run under `if __name__ == "__main__":`, as it uses multiprocessing.
- The methods which are under `register_rpc()` in `ZeroServer` should have **type hinting**, like `def echo(msg: str):`

## Let's do some benchmarking 🤘

Zero is talking about inter service communication. In most real life scenarios, we need to call another microservice.

So we will be testing a gateway calling another server for some data. Check the [benchmark/dockerize](https://github.com/Ananto30/zero/tree/main/benchmarks/dockerize) folder for details.

There are two endpoints in every tests,

- `/hello`: Just call for a hello world response 😅
- `/order`: Save a Order object in redis

Compare the results! 👇

## Benchmarks 🏆


On my pc, core i3-10100 CPU @ 3.60GHz, 16GB ram with docker limits, **cpu 40% and memory 256m**, I got the following results -

| Framework | "hello world" example | redis save example |
| --------- | --------------------- | ------------------ |
| aiohttp   | 1,424.24 req/s        | 256.15 req/s       |
| fastApi   | 980.42 req/s          | 252.08 req/s       |
| sanic     | 3,085.80 req/s        | 547.02 req/s       |
| zero      | 5,000.77 req/s        | 784.51 req/s       |


Here is the result on MacBook Pro (13-inch, M1, 2020), Apple M1, 8 cores (4 performance and 4 efficiency), 8 GB RAM

| Framework | "hello world" example | redis save example |
| --------- | --------------------- | ------------------ |
| aiohttp   | 12,409.50 req/s       | 6,161.43 req/s     |
| fastApi   | 8,653.16 req/s        | 5,727.53 req/s     |
| sanic     | 22,644.41 req/s       | 7,750.49 req/s     |
| zero      | 15,853.92 req/s       | 11,167.89 req/s    |

More about MacBook benchmarks [here](https://github.com/Ananto30/zero/blob/main/benchmarks/others/mac-results.md)


## Todo list 📃

- Add pydantic support
- Code generation for pydantic models
- Improve error handling
- Fault tolerance

## Contribution

Contributors are welcomed 🙏

**Please leave a star ⭐ if you like Zero!**
