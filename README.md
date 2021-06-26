<p align="center">
    <img height="500px" src="https://ananto30.github.io/i/1200xCL_TP.png" /> 
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

*(Work in progress)*

Zero is a high performance and fast (see [benchmarks](https://github.com/Ananto30/zero#benchmarks)) Python microservice framework that provides RPC and Pub Sub interface.

**Features**: 
- Zero provides **faster communication** between the microservices using [zeromq](https://zeromq.org/) under the hood.
- Zero uses messages for communication and traditional **client-server** or **request-reply** pattern is supported. 
- Support for both **Async** and **sync**.
- The base server (ZeroServer) **utilizes all cpu cores**.

**Philosophy** behind Zero: 
- **Zero learning curve**: The learning curve is tends to zero. You just add your functions and spin up a server, literally that's it! 
The framework hides the complexity of messaging pattern that enables faster communication. 
- **ZeroMQ**: An awesome messaging library enables the power of Zero.

Take a look at an example server [here](https://github.com/Ananto30/zero/tree/develop/examples/basic).

### Tired of hearing buzzwords? Let's test!

Zero is talking about inter service communication. In most real life scenarios, we need to call another microservice. 

So we will be testing a server (gateway) calling another server for some data. (In the `benchmarks` folder, you can find more)

There are two endpoints in every tests, 
- `/hello`: Just call for a hello world response 😅
- `/order`: Save a Order object in redis (ensure running `redis-server` first)


*Ensure Python 3.7+*

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

## Example

- Create a `server.py`
```python
from zero import ZeroServer


def echo(msg):
    return msg


async def hello_world(msg):
    return "hello world"


if __name__ == "__main__":
    app = ZeroServer(port=5559)
    app.register_rpc(echo)
    app.register_rpc(hello_world)
    app.run()

```
See the method type async or sync, doesn't matter.

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
    resp = await zero_client.call_async("hello_world", "")
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
    resp = zero_client.call("hello_world", "")
    print(resp)


if __name__ == "__main__":
    echo()
    hello()

```

## Benchmarks

Here is the result on MacBook Pro (16-inch, 2019), 2.6 GHz 6-Core Intel Core i7, 16 GB 2667 MHz DDR4

For aiohttp -
```
> wrk -d10s -t50 -c200 http://127.0.0.1:8000/hello
Running 10s test @ http://127.0.0.1:8000/hello
  50 threads and 200 connections
  Thread Stats   Avg      Stdev     Max   +/- Stdev
    Latency   112.02ms  136.57ms 665.72ms   82.15%
    Req/Sec    60.74     44.44   200.00     60.98%
  15202 requests in 10.10s, 2.44MB read
Requests/sec:   1504.41
Transfer/sec:    246.82KB

> wrk -d10s -t50 -c200 http://127.0.0.1:8000/order
Running 10s test @ http://127.0.0.1:8000/order
  50 threads and 200 connections
  Thread Stats   Avg      Stdev     Max   +/- Stdev
    Latency   148.15ms   95.78ms 772.12ms   74.66%
    Req/Sec    29.10     13.99    90.00     70.95%
  14191 requests in 10.10s, 3.41MB read
Requests/sec:   1404.88
Transfer/sec:    345.80KB
```

For sanic -
```
> wrk -d10s -t50 -c200 http://127.0.0.1:8000/hello
Running 10s test @ http://127.0.0.1:8000/hello
  50 threads and 200 connections
  Thread Stats   Avg      Stdev     Max   +/- Stdev
    Latency   372.58ms  225.79ms   1.18s    57.34%
    Req/Sec    13.19      9.26    50.00     79.10%
  5299 requests in 10.10s, 595.10KB read
  Socket errors: connect 0, read 138, write 0, timeout 0
Requests/sec:    524.46
Transfer/sec:     58.90KB

> wrk -d10s -t50 -c200 http://127.0.0.1:8000/order
Running 10s test @ http://127.0.0.1:8000/order
  50 threads and 200 connections
  Thread Stats   Avg      Stdev     Max   +/- Stdev
    Latency   458.77ms  411.95ms   1.76s    65.57%
    Req/Sec    17.53     21.77   120.00     86.83%
  4622 requests in 10.10s, 803.43KB read
  Socket errors: connect 0, read 11, write 0, timeout 0
Requests/sec:    457.76
Transfer/sec:     79.57KB
```

For fastApi -
```
> wrk -d10s -t50 -c200 http://127.0.0.1:8000/hello
Running 10s test @ http://127.0.0.1:8000/hello
  50 threads and 200 connections
  Thread Stats   Avg      Stdev     Max   +/- Stdev
    Latency   503.64ms  336.89ms   1.71s    86.45%
    Req/Sec     9.88      6.27    40.00     71.45%
  4066 requests in 10.08s, 547.96KB read
  Socket errors: connect 0, read 69, write 0, timeout 4
Requests/sec:    403.25
Transfer/sec:     54.34KB

> wrk -d10s -t50 -c200 http://127.0.0.1:8000/order
Running 10s test @ http://127.0.0.1:8000/order
  50 threads and 200 connections
  Thread Stats   Avg      Stdev     Max   +/- Stdev
    Latency   533.32ms  541.91ms   1.96s    80.37%
    Req/Sec    18.05     21.29   111.00     84.02%
  3945 requests in 10.09s, 824.44KB read
  Socket errors: connect 0, read 96, write 0, timeout 71
Requests/sec:    391.09
Transfer/sec:     81.73KB
```

For zero -
```
> wrk -d10s -t50 -c200 http://127.0.0.1:8000/hello
Running 10s test @ http://127.0.0.1:8000/hello
  50 threads and 200 connections
  Thread Stats   Avg      Stdev     Max   +/- Stdev
    Latency    21.43ms   11.23ms 145.58ms   72.29%
    Req/Sec   190.72     75.47     1.09k    74.25%
  95331 requests in 10.10s, 15.27MB read
Requests/sec:   9436.16
Transfer/sec:      1.51MB

> wrk -d10s -t50 -c200 http://127.0.0.1:8000/order
Running 10s test @ http://127.0.0.1:8000/order
  50 threads and 200 connections
  Thread Stats   Avg      Stdev     Max   +/- Stdev
    Latency    25.32ms   11.09ms 132.30ms   70.02%
    Req/Sec   160.10     43.03   363.00     71.97%
  80035 requests in 10.08s, 19.69MB read
Requests/sec:   7936.92
Transfer/sec:      1.95MB
```
