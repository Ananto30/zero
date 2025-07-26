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
    <a href="https://pepy.tech/project/zeroapi" target="_blank">
        <img src="https://static.pepy.tech/badge/zeroapi" />
    </a>
</p>

<hr>

**Features**:

* Zero provides **faster communication** (see [benchmarks](https://github.com/Ananto30/zero#benchmarks-)) between the microservices using [zeromq](https://zeromq.org/) under the hood.
* Zero uses messages for communication and traditional **client-server** or **request-reply** pattern is supported.
* Support for both **async** and **sync**.
* The base server (ZeroServer) **utilizes all cpu cores**.
* Built-in support for Pydantic.
* **Code generation**! See [example](https://github.com/Ananto30/zero#code-generation-) 👇

**Philosophy** behind Zero:

* **Zero learning curve**: The learning curve is tends to zero. Just add functions and spin up a server, literally that's it! The framework hides the complexity of messaging pattern that enables faster communication.
* **ZeroMQ**: An awesome messaging library enables the power of Zero.

Let's get started!

# Getting started 🚀

*Ensure Python 3.8+*

```
pip install zeroapi
```

**For Windows**, [tornado](https://pypi.org/project/tornado/) needs to be installed separately (for async operations). It's not included with `zeroapi` because for linux and mac-os, tornado is not needed as they have their own event loops.

* Create a `server.py`

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

* The **RPC functions only support one argument** (`msg`) for now.

* Also note that server **RPC functions are type hinted**. Type hint is **must** in Zero server. Supported types can be found [here](/zero/utils/type_util.py#L11).

* Run the server

  ```shell
  python -m server
  ```

* Call the rpc methods

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

* Or using async client -

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

# Serialization 📦

## Default serializer

[Msgspec](https://jcristharif.com/msgspec/) is the default serializer. So `msgspec.Struct` (for high performance) or `dataclass` or any [supported types](https://jcristharif.com/msgspec/supported-types.html) can be used easily to pass complex arguments, i.e.

```python
from dataclasses import dataclass
from msgspec import Struct
from zero import ZeroServer

app = ZeroServer()

class Person(Struct):
    name: str
    age: int
    dob: datetime

@dataclass
class Order:
    id: int
    amount: float
    created_at: datetime

@app.register_rpc
def save_person(person: Person) -> bool:
    # save person to db
    ...

@app.register_rpc
def save_order(order: Order) -> bool:
    # save order to db
    ...
```

## Return type on client

The return type of the RPC function can be any of the [supported types](https://jcristharif.com/msgspec/supported-types.html). If `return_type` is set in the client `call` method, then the return type will be converted to that type.

```python
@dataclass
class Order:
    id: int
    amount: float
    created_at: datetime

def get_order(id: str) -> Order:
    return zero_client.call("get_order", id, return_type=Order)
```

# Code Generation 🤖

Easy to use code generation tool is also provided with schema support!

* After running the server, like above, it calls the server to get the client code.

  This makes it easy to get the latest schemas on live servers and not to maintain other file sharing approach to manage schemas.

  Using `zero.generate_client` generate client code for even remote servers using the `--host` and `--port` options.

  ```shell
  python -m zero.generate_client --host localhost --port 5559 --overwrite-dir ./my_client
  ```

* It will generate client like this -

  ```python
  from dataclasses import dataclass
  from msgspec import Struct
  from datetime import datetime

  from zero import ZeroClient


  zero_client = ZeroClient("localhost", 5559)

  class Person(Struct):
      name: str
      age: int
      dob: datetime


  @dataclass
  class Order:
      id: int
      amount: float
      created_at: datetime


  class RpcClient:
      def __init__(self, zero_client: ZeroClient):
          self._zero_client = zero_client

      def save_person(self, person: Person) -> bool:
          return self._zero_client.call("save_person", person)

      def save_order(self, order: Order) -> bool:
          return self._zero_client.call("save_order", order)
  ```

  Check the schemas are copied!

* Use the client -

  ```python
  from my_client import RpcClient, zero_client

  client = RpcClient(zero_client)

  if __name__ == "__main__":
      client.save_person(Person(name="John", age=25, dob=datetime.now()))
      client.save_order(Order(id=1, amount=100.0, created_at=datetime.now()))
  ```

*If you want a async client just replace `ZeroClient` with `AsyncZeroClient` in the generated code, and update the methods to be async. (Next version will have async client generation, hopefully 😅)*

# Important notes! 📝

## For multiprocessing

* `ZeroServer` should always be run under `if __name__ == "__main__":`, as it uses multiprocessing.
* `ZeroServer` creates the workers in different processes, so anything global in your code will be instantiated N times where N is the number of workers. So if you want to initiate them once, put them under `if __name__ == "__main__":`. But recommended to not use global vars. And Databases, Redis, other clients, creating them N times in different processes is fine and preferred.

# Let's do some benchmarking! 🏎

Zero is all about inter service communication. In most real life scenarios, we need to call another microservice.

So we will be testing a gateway calling another server for some data. Check the [benchmark/dockerize](https://github.com/Ananto30/zero/tree/main/benchmarks/dockerize) folder for details.

There are two endpoints in every tests,

* `/hello`: Just call for a hello world response 😅
* `/order`: Save a Order object in redis

Compare the results! 👇

# Benchmarks 🏆

13th Gen Intel® Core™ i9-13900HK @ 5.40GHz, 14 cores, 20 threads, 32GB RAM (Docker in Ubuntu 22.04.2 LTS)

*(Sorted alphabetically)*

| Framework   | "hello world" (req/s) | 99% latency (ms) | redis save (req/s) | 99% latency (ms) |
| ----------- | --------------------- | ---------------- | ------------------ | ---------------- |
| aiohttp     | 35023.07              | 7.66             | 17153.06           | 12.09            |
| aiozmq      | 20621.64              | 6.88             | 7651.61            | 11.13            |
| blacksheep  | 21887.95              | 8.9              | 11446.89           | 15.77            |
| fastApi     | 19857.4               | 9.66             | 9781.64            | 18.58            |
| sanic       | 46143.93              | 5.22             | 20062.11           | 9.77             |
| zero(sync)  | 22556.58              | 8.86             | 11779.06           | 20.13            |
| zero(async) | 34411.23              | 5.73             | 23638.82           | 8.13             |

Seems like sanic is the fastest in hello world response, but zero is the fastest in redis save 🎉

# Contribution

Contributors are welcomed 🙏

**Please leave a star ⭐ if you like Zero!**

[!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/ananto30)
