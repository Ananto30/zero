# Dockerized Benchmarks

This is a good way to benchmark the frameworks inside Docker with limitation like cpu and memory.

Check the docker-compose files inside each framework. They are limited using -

```yml
cpus: "0.40"
mem_limit: 256m
```

You can play with these to test things.

## Run

Just use the makefile!
Run becnhmarks for a framework -

```bash
make benchmark-aiohttp
```

Or

```bash
make benchmark-zero
```

## Settings to play with

### Workers count

In the `docker-compose.yml` you can play with the `--workers` count of gateway and server service. Like as my machine is 4 core 8 thread, I put `--workers 8`. So depending on your machine, use decent/clever numbers.

### wrk threads and connections

If you know the `wrk` well, just play with the configs. If you are naive like me, threads are basically your cpu threads (or 2x cpu threads). If you increase them no harm done, but it won't perform well I guess and connections are basically number of concurrent requests distributed amond the threads. You have to figure this out, if you start increasing the number, at one point your results will be saturated and servers will start to drop connections. That's the maximum you can reach.

I have used 2x cpu threads so `-t 16` and 16x25 = 400 connections.

## Latest benchmark results

11th Gen Intel(R) Core(TM) i7-1165G7 @ 2.80GHz, 4 cores, 8 threads, 12GB RAM

*(Sorted alphabetically)*

| Framework | "hello world" (req/s) | 99% latency (ms) | redis save (req/s) | 99% latency (ms) |
| --------- | --------------------- | ---------------- | ------------------ | ---------------- |
| aiohttp   | 9553.16               | 25.48            | 5497.03            | 27.90            |
| aiozmq    | 13241.74              | 12.12            | 5087.68            | 21.59            |
| fastApi   | 6036.61               | 31.28            | 3648.11            | 50.76            |
| sanic     | 13195.99              | 20.04            | 7226.72            | 25.24            |
| zero      | 18867.00              | 11.48            | 12293.81           | 11.68            |

## Old benchmark results

Intel Core i3 10100, 4 cores, 8 threads, 16GB RAM, with docker limits **cpu 40% and memory 256m**

*(Sorted alphabetically)*

| Framework | "hello world" example | redis save example |
| --------- | --------------------- | ------------------ |
| aiohttp   | 1,424.24 req/s        | 256.15 req/s       |
| aiozmq    | 1,840.40 req/s        | 712.22 req/s       |
| fastApi   | 980.42 req/s          | 252.08 req/s       |
| sanic     | 3,085.80 req/s        | 547.02 req/s       |
| zero      | 5,000.77 req/s        | 784.51 req/s       |

MacBook Pro (13-inch, M1, 2020), Apple M1, 8 cores (4 performance and 4 efficiency), 8 GB RAM

*(Sorted alphabetically)*

| Framework | "hello world" example | redis save example |
| --------- | --------------------- | ------------------ |
| aiohttp   | 12,409.50 req/s       | 6,161.43 req/s     |
| fastApi   | 8,653.16 req/s        | 5,727.53 req/s     |
| sanic     | 22,644.41 req/s       | 7,750.49 req/s     |
| zero      | 15,853.92 req/s       | 11,167.89 req/s    |

More about MacBook benchmarks [here](https://github.com/Ananto30/zero/blob/main/benchmarks/others/mac-results.md)

### Note

Please note that sometimes just `docker-compose up` will not run the `wrk`. Because you know about the docker `depends_on` only ensures the service is up, not running or healthy. So you may need to run wrk service after other services are up and running.
