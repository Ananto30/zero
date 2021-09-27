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
</p>
<hr>


Zero is a high performance and fast (see [benchmarks](https://github.com/Ananto30/zero#benchmarks-)) Python microservice framework that provides RPC and Pub Sub interface.

**Features**: 
- Zero provides **faster communication** between the microservices using [zeromq](https://zeromq.org/) under the hood.
- Zero uses messages for communication and traditional **client-server** or **request-reply** pattern is supported. 
- Support for both **Async** and **sync**.
- The base server (ZeroServer) **utilizes all cpu cores**.

**Philosophy** behind Zero: 
- **Zero learning curve**: The learning curve is tends to zero. You just add your functions and spin up a server, literally that's it! 
The framework hides the complexity of messaging pattern that enables faster communication. 
- **ZeroMQ**: An awesome messaging library enables the power of Zero.

Let's get started!


## Getting started 🚀
*Ensure Python 3.8+*
```
pip install zeroapi
```



- Create a `server.py`
```python
from zero import ZeroServer

def echo(msg: str):
    return msg

async def hello_world():
    return "hello world"


if __name__ == "__main__":
    app = ZeroServer(port=5559)
    app.register_rpc(echo)
    app.register_rpc(hello_world)
    app.run()

```
Please note that server **RPC methods' args are type hinted**. Type hint is **must** in Zero server.

*See the method type async or sync, doesn't matter.* 😃

- Run it
```
python -m server
```

- Call the rpc methods
```python
import asyncio

from zero import ZeroClient

zero_client = ZeroClient("localhost", 5559)

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

Or using sync client -
```python
from zero import ZeroClient

zero_client = ZeroClient("localhost", 5559, use_async=False)

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

## Important notes
- `ZeroServer` should always be run under `if __name__ == "__main__":`, as it uses multiprocessing.
- The methods which are under `register_rpc()` in `ZeroServer` should have **type hinting**, like `def echo(msg: str):`

## Tired of hearing buzzwords? Let's test! 🤘

Zero is talking about inter service communication. In most real life scenarios, we need to call another microservice. 

So we will be testing a server (gateway) calling another server for some data. (In the `benchmarks` folder, you can find more)

There are two endpoints in every tests, 
- `/hello`: Just call for a hello world response 😅
- `/order`: Save a Order object in redis (ensure running `redis-server` first)


*Ensure Python 3.8+*

- Setup 
    ```zsh
    git clone https://github.com/Ananto30/zero.git
    cd zero
    python3 -m venv venv
    source venv/bin/activate
    pip install -r benchmarks/requirements.txt
    ```


- Test the current fast framework in Python (aiohttp, sanic, fastApi etc.)

    Run the gateway and server -
    ```
    sh benchmarks/asyncio/run_both.sh
    ```
    Run the benchmark using your favorite tool -
    ```
    $ wrk -d10s -t50 -c200 http://127.0.0.1:8000/hello
    ```


- Test Zero

    Run the gateway and server -
    ```
    sh benchmarks/zero/run_both.sh
    ```
    Run the benchmark using your favorite tool -
    ```
    $ wrk -d10s -t50 -c200 http://127.0.0.1:8000/hello
    ```

Compare the results! Or just see the [benchmarks](https://github.com/Ananto30/zero#benchmarks).

## Benchmarks 🏆

Here is the result on MacBook Pro (13-inch, M1, 2020), Apple M1, 8 cores (4 performance and 4 efficiency), 8 GB RAM

For aiohttp -
```
> wrk -d10s -t8 -c240 http://127.0.0.1:8000/hello
Running 10s test @ http://127.0.0.1:8000/hello
  8 threads and 240 connections
  Thread Stats   Avg      Stdev     Max   +/- Stdev
    Latency    35.06ms   44.90ms 412.88ms   84.98%
    Req/Sec     1.56k   444.76     5.09k    77.25%
  124255 requests in 10.01s, 19.91MB read
  Socket errors: connect 0, read 102, write 0, timeout 0
Requests/sec:  12409.50
Transfer/sec:      1.99MB

> wrk -d10s -t8 -c240 http://127.0.0.1:8000/order
Running 10s test @ http://127.0.0.1:8000/order
  8 threads and 240 connections
  Thread Stats   Avg      Stdev     Max   +/- Stdev
    Latency    50.83ms   52.31ms 386.97ms   83.64%
    Req/Sec   774.89    219.09     1.73k    69.62%
  61807 requests in 10.03s, 14.85MB read
  Socket errors: connect 0, read 101, write 0, timeout 0
Requests/sec:   6161.43
Transfer/sec:      1.48MB
```

For sanic -
```
> wrk -d10s -t8 -c240 http://127.0.0.1:8000/hello
Running 10s test @ http://127.0.0.1:8000/hello
  8 threads and 240 connections
  Thread Stats   Avg      Stdev     Max   +/- Stdev
    Latency    13.69ms   14.63ms 171.07ms   87.96%
    Req/Sec     2.85k     1.00k    6.25k    76.12%
  226992 requests in 10.02s, 24.89MB read
  Socket errors: connect 0, read 141, write 0, timeout 0
Requests/sec:  22644.41
Transfer/sec:      2.48MB

> wrk -d10s -t8 -c240 http://127.0.0.1:8000/order
Running 10s test @ http://127.0.0.1:8000/order
  8 threads and 240 connections
  Thread Stats   Avg      Stdev     Max   +/- Stdev
    Latency    42.91ms   45.96ms 320.13ms   83.70%
    Req/Sec     0.98k   277.75     2.04k    70.96%
  77888 requests in 10.05s, 13.22MB read
  Socket errors: connect 0, read 126, write 0, timeout 0
Requests/sec:   7750.49
Transfer/sec:      1.32MB
```

For fastApi -
```
> wrk -d10s -t8 -c240 http://127.0.0.1:8000/hello
Running 10s test @ http://127.0.0.1:8000/hello
  8 threads and 240 connections
  Thread Stats   Avg      Stdev     Max   +/- Stdev
    Latency    30.33ms   24.27ms 215.15ms   68.17%
    Req/Sec     1.09k   348.97     2.36k    70.00%
  86908 requests in 10.04s, 11.44MB read
  Socket errors: connect 0, read 97, write 0, timeout 0
Requests/sec:   8653.16
Transfer/sec:      1.14MB

> wrk -d10s -t8 -c240 http://127.0.0.1:8000/order
Running 10s test @ http://127.0.0.1:8000/order
  8 threads and 240 connections
  Thread Stats   Avg      Stdev     Max   +/- Stdev
    Latency    43.16ms   27.80ms 283.60ms   68.00%
    Req/Sec   720.17    124.58     1.24k    71.62%
  57490 requests in 10.04s, 11.73MB read
  Socket errors: connect 0, read 100, write 0, timeout 0
Requests/sec:   5727.53
Transfer/sec:      1.17MB
```

For zero -
```
> wrk -d10s -t8 -c240 http://127.0.0.1:8000/hello
Running 10s test @ http://127.0.0.1:8000/hello
  8 threads and 240 connections
  Thread Stats   Avg      Stdev     Max   +/- Stdev
    Latency    15.10ms    9.91ms  43.16ms   47.27%
    Req/Sec     1.99k   777.55     3.64k    70.50%
  158706 requests in 10.01s, 25.43MB read
  Socket errors: connect 0, read 101, write 0, timeout 0
Requests/sec:  15853.92
Transfer/sec:      2.54MB

> wrk -d10s -t8 -c240 http://127.0.0.1:8000/order
Running 10s test @ http://127.0.0.1:8000/order
  8 threads and 240 connections
  Thread Stats   Avg      Stdev     Max   +/- Stdev
    Latency    24.59ms   21.15ms  94.09ms   62.77%
    Req/Sec     1.42k   614.40     8.39k    60.80%
  112807 requests in 10.10s, 27.76MB read
  Socket errors: connect 0, read 102, write 0, timeout 0
Requests/sec:  11167.89
Transfer/sec:      2.75MB
```

From the above numbers we can see only sanic has higher "hello world" performance than zero but again loses in the real-life example of redis order saving.

In short - 

Framework | "hello world" example | redis save example
--- | --- | ---
aiohttp | 12409.50 req/s | 6161.43 req/s
sanic | 22644.41 req/s | 7750.49 req/s
fastApi | 8653.16 req/s | 5727.53 req/s
zero | 15853.92 req/s | 11167.89 req/s


## Todo list 📃
- Graceful shutdown server
- Improve error handling
- Fault tolerance

## Contribution
Contributors are welcomed 🙏

**Please leave a star ⭐ if you like Zero!**