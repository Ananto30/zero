<p align="center">
    <img height="300px" src="https://ananto30.github.io/i/1200xCL_TP.png" />
</p>
<p align="center">
    <em>Zero is a simple Python framework (RPC like) to build fast and high performance microservices or distributed servers</em>
</p>
<p align="center">
    <a href="https://codecov.io/gh/Ananto30/zero" target="_blank">
        <img src="https://codecov.io/gh/Ananto30/zero/branch/main/graph/badge.svg?token=k0aA0G6NLs" />
    </a>
    <a href="https://pypi.org/project/zeroapi/" target="_blank">
        <img src="https://img.shields.io/pypi/v/zeroapi" />
    </a>
    <br>
    <a href="https://app.codacy.com/gh/Ananto30/zero/dashboard?utm_source=gh&utm_medium=referral&utm_content=&utm_campaign=Badge_grade">
        <img src="https://app.codacy.com/project/badge/Grade/f6d4db49974b470f95999565f7901595"/>
    </a>
    <a href="https://codeclimate.com/github/Ananto30/zero/maintainability" target="_blank">
        <img src="https://api.codeclimate.com/v1/badges/4f2fd83bee97326699bc/maintainability" />
    </a>
</p>
<hr>

**Features**:

*   Zero provides **faster communication** (see [benchmarks](https://github.com/Ananto30/zero#benchmarks-)) between the microservices using [zeromq](https://zeromq.org/) under the hood.
*   Zero uses messages for communication and traditional **client-server** or **request-reply** pattern is supported.
*   Support for both **Async** and **sync**.
*   The base server (ZeroServer) **utilizes all cpu cores**.
*   **Code generation**! See [example](https://github.com/Ananto30/zero#code-generation-) 👇

**Philosophy** behind Zero:

*   **Zero learning curve**: The learning curve is tends to zero. You just add your functions and spin up a server, literally that's it! The framework hides the complexity of messaging pattern that enables faster communication.
*   **ZeroMQ**: An awesome messaging library enables the power of Zero.

Let's get started!

# Getting started 🚀

*Ensure Python 3.8+*

    pip install zeroapi

**For Windows**, [tornado](https://pypi.org/project/tornado/) needs to be installed separately (for async operations). It's not included with `zeroapi` because for linux and mac-os, tornado is not needed as they have their own event loops.

*   Create a `server.py`

```python
from zero import ZeroServer

app = ZeroServer(port=5559)

@app.register_rpc
def echo(msg: str) -> str:
    return msg

@app.register_rpc
async def hello_world() -> str:
    return "hello world"


if __name__ == "__main__":
    app.run()
```

Please note that server **RPC methods are type hinted**. Type hint is **must** in Zero server.

*See the method type async or sync, doesn't matter.* 😃

*   Run it

<!---->

    python -m server

*   Call the rpc methods

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

from zero import AsyncZeroClient

zero_client = AsyncZeroClient("localhost", 5559)

async def echo():
    resp = await zero_client.call("echo", "Hi there!")
    print(resp)

async def hello():
    resp = await zero_client.call("hello_world", None)
    print(resp)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(echo())
    loop.run_until_complete(hello())
```

# Code Generation! 🙌

You can also use our code generation tool to generate Python client code!

After running the server, like above, you can call the server to get the client code.

Using `zero.generate_client` you can generate client code for even remote servers using the `--host` and `--port` options. You don't need access to the code 😃

```shell
python -m zero.generate_client --host localhost --port 5559 --overwrite-dir ./my_client
```

It will generate client like this -

```python
import typing  # remove this if not needed
from typing import List, Dict, Union, Optional, Tuple  # remove this if not needed
from zero import ZeroClient


zero_client = ZeroClient("localhost", 5559)


class RpcClient:
    def __init__(self, zero_client: ZeroClient):
        self._zero_client = zero_client

    def echo(self, msg: str) -> str:
        return self._zero_client.call("echo", msg)

    def hello_world(self, msg: str) -> str:
        return self._zero_client.call("hello_world", msg)
```

Use the client -

```python
from my_client import RpcClient, zero_client

client = RpcClient(zero_client)

if __name__ == "__main__":
    client.echo("Hi there!")
    client.hello_world(None)
```

Currently, the code generation tool supports only `ZeroClient` and not `AsyncZeroClient`.

# Important notes 📝

*   `ZeroServer` should always be run under `if __name__ == "__main__":`, as it uses multiprocessing.
*   The methods which are under `register_rpc()` in `ZeroServer` should have **type hinting**, like `def echo(msg: str):`

# Let's do some benchmarking 🤘

Zero is talking about inter service communication. In most real life scenarios, we need to call another microservice.

So we will be testing a gateway calling another server for some data. Check the [benchmark/dockerize](https://github.com/Ananto30/zero/tree/main/benchmarks/dockerize) folder for details.

There are two endpoints in every tests,

*   `/hello`: Just call for a hello world response 😅
*   `/order`: Save a Order object in redis

Compare the results! 👇

# Benchmarks 🏆

11th Gen Intel® Core™ i7-11800H @ 2.30GHz, 8 cores, 16 threads, 16GB RAM (Docker in Ubuntu 22.04.2 LTS)

*(Sorted alphabetically)*

Framework   | "hello world" (req/s) | 99% latency (ms) | redis save (req/s) | 99% latency (ms)
----------- | --------------------- | ---------------- | ------------------ | ----------------
aiohttp     | 14391.38              | 10.96            | 9470.74            | 12.94
aiozmq      | 15121.86              | 9.42             | 5904.84            | 21.57
fastApi     | 9590.96               | 18.31            | 6669.81            | 24.41
sanic       | 18790.49              | 8.69             | 12259.29           | 13.52
zero(sync)  | 24805.61              | 4.57             | 16498.83           | 7.80
zero(async) | 22716.84              | 5.61             | 17446.19           | 7.24

# Roadmap 🗺

*   \[ ] Make msgspec as default serializer
*   \[ ] Add support for async server (currently the sync server runs async functions in the eventloop, which is blocking)
*   \[ ] Add pub/sub support

# Contribution

Contributors are welcomed 🙏

**Please leave a star ⭐ if you like Zero!**

[!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/ananto30)
