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

I have used cpu threads so `-t 8` and 8x10 = 80 connections.

## History

You can check the history of the benchmarks in the `history` folder. It contains the results of previous runs, which can be useful for comparison and analysis.

### Note

Please note that sometimes just `docker-compose up` will not run the `wrk`. Because you know about the docker `depends_on` only ensures the service is up, not running or healthy. So you may need to run wrk service after other services are up and running.
