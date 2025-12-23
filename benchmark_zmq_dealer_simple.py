#!/usr/bin/env python3
"""
Benchmark comparing REP/REQ vs ROUTER/DEALER socket patterns.

REP/REQ: Sequential request-reply (one request at a time, strict ordering)
ROUTER/DEALER: Asynchronous pattern (can handle multiple concurrent messages)

ROUTER/DEALER is the recommended async pattern for ZMQ when you need
true concurrent message handling without strict request-reply semantics.
"""
import asyncio
import multiprocessing
import sys
import time

import zmq
import zmq.asyncio


def sync_rep_server(port: int, num_requests: int):
    """Sync REP server - handles one request at a time sequentially."""
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind(f"tcp://127.0.0.1:{port}")

    received = 0
    while received < num_requests:
        request = socket.recv()
        received += 1
        # Simulate some work
        time.sleep(0.0001)
        socket.send(b"OK")

    socket.close()
    context.term()


def sync_router_server(port: int, num_requests: int):
    """Sync ROUTER server - handles multiple concurrent messages."""
    context = zmq.Context()
    socket = context.socket(zmq.ROUTER)
    socket.bind(f"tcp://127.0.0.1:{port}")

    poller = zmq.Poller()
    poller.register(socket, zmq.POLLIN)

    received = 0
    while received < num_requests:
        events = dict(poller.poll(1000))  # 1 second timeout
        if socket in events:
            # ROUTER format: [identity, empty, message]
            frames = socket.recv_multipart()
            received += 1
            # Simulate some work
            time.sleep(0.0001)
            # Send back to client (must include identity)
            socket.send_multipart([frames[0], b"", b"OK"])

    socket.close()
    context.term()


async def async_rep_server(port: int, num_requests: int):
    """Async REP server - sequential request-reply."""
    context = zmq.asyncio.Context()
    socket = context.socket(zmq.REP)
    socket.bind(f"tcp://127.0.0.1:{port}")

    received = 0
    while received < num_requests:
        request = await socket.recv()
        received += 1
        # Simulate some work
        await asyncio.sleep(0.0001)
        await socket.send(b"OK")

    socket.close()


async def async_router_server(port: int, num_requests: int):
    """Async ROUTER server - concurrent message handling with poller."""
    context = zmq.asyncio.Context()
    socket = context.socket(zmq.ROUTER)
    socket.bind(f"tcp://127.0.0.1:{port}")

    poller = zmq.asyncio.Poller()
    poller.register(socket, zmq.POLLIN)

    received = 0
    while received < num_requests:
        events = await poller.poll(1000)
        event_dict = dict(events)
        if socket in event_dict:
            # ROUTER format: [identity, empty, message]
            frames = await socket.recv_multipart()
            received += 1
            # Simulate some work
            await asyncio.sleep(0.0001)
            # Send back to client (must include identity)
            await socket.send_multipart([frames[0], b"", b"OK"])

    socket.close()


def req_client_worker(port: int, num_requests: int):
    """REQ client worker - synchronous request-reply."""
    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    socket.connect(f"tcp://127.0.0.1:{port}")

    for i in range(num_requests):
        socket.send(b"REQUEST")
        response = socket.recv()

    socket.close()
    context.term()


def dealer_client_worker(port: int, num_requests: int):
    """DEALER client worker - asynchronous messaging."""
    context = zmq.Context()
    socket = context.socket(zmq.DEALER)
    socket.connect(f"tcp://127.0.0.1:{port}")

    for i in range(num_requests):
        socket.send(b"REQUEST")
        response = socket.recv()

    socket.close()
    context.term()


def run_benchmark(
    server_func,
    client_worker_func,
    port: int,
    num_clients: int,
    requests_per_client: int,
    name: str,
):
    """Run a complete benchmark test."""
    print(f"\n{'='*60}")
    print(f"{name}")
    print(f"{'='*60}")
    print(f"Clients: {num_clients}, Requests/client: {requests_per_client}")

    total_requests = num_clients * requests_per_client

    # Start server
    if asyncio.iscoroutinefunction(server_func):
        server_process = None
    else:
        server_process = multiprocessing.Process(target=server_func, args=(port, total_requests))
        server_process.start()
        time.sleep(0.5)  # Give server time to start

    # Start clients
    start_time = time.time()

    if not server_process:
        # Run async server
        async def run_async():
            # Start server in background
            server_task = asyncio.create_task(server_func(port, total_requests))

            # Give server time to bind
            await asyncio.sleep(0.5)

            # Start client workers
            clients = [
                asyncio.create_task(
                    asyncio.to_thread(client_worker_func, port, requests_per_client)
                )
                for _ in range(num_clients)
            ]

            # Wait for all clients to finish
            await asyncio.gather(*clients)

            # Wait for server to finish
            await server_task

        asyncio.run(run_async())
    else:
        # Run sync clients
        processes = [
            multiprocessing.Process(target=client_worker_func, args=(port, requests_per_client))
            for _ in range(num_clients)
        ]

        for p in processes:
            p.start()

        for p in processes:
            p.join()

        server_process.join()

    elapsed = time.time() - start_time
    rps = total_requests / elapsed if elapsed > 0 else 0

    print(f"Time: {elapsed:.3f}s")
    print(f"RPS: {rps:,.0f} req/sec")

    return rps, elapsed


def main():
    num_clients = 10
    requests_per_client = 1000

    results = {}

    # Test 1: Sync REP/REQ (baseline)
    rps, t = run_benchmark(
        sync_rep_server,
        req_client_worker,
        5555,
        num_clients,
        requests_per_client,
        "SYNC REP/REQ SERVER (Sequential)",
    )
    results["Sync REP/REQ"] = (rps, t)

    # Test 2: Sync ROUTER/DEALER with polling
    rps, t = run_benchmark(
        sync_router_server,
        dealer_client_worker,
        5556,
        num_clients,
        requests_per_client,
        "SYNC ROUTER/DEALER SERVER (Concurrent)",
    )
    results["Sync ROUTER/DEALER"] = (rps, t)

    # Test 3: Async REP/REQ
    rps, t = run_benchmark(
        async_rep_server,
        req_client_worker,
        5557,
        num_clients,
        requests_per_client,
        "ASYNC REP/REQ SERVER (Sequential)",
    )
    results["Async REP/REQ"] = (rps, t)

    # Test 4: Async ROUTER/DEALER
    rps, t = run_benchmark(
        async_router_server,
        dealer_client_worker,
        5558,
        num_clients,
        requests_per_client,
        "ASYNC ROUTER/DEALER SERVER (Concurrent)",
    )
    results["Async ROUTER/DEALER"] = (rps, t)

    # Print summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")

    max_rps = max(rps for rps, _ in results.values())

    for name, (rps, elapsed) in results.items():
        ratio = rps / max_rps if max_rps > 0 else 0
        print(f"{name:35} {rps:>12,.0f} RPS  {elapsed:>6.3f}s  ({ratio:.2f}x)")

    fastest_name = max(results.items(), key=lambda x: x[1][0])[0]
    print(f"\nFastest: {fastest_name}")

    # Print insights
    print(f"\n{'='*60}")
    print("INSIGHTS")
    print(f"{'='*60}")
    print("REP/REQ is strictly sequential - one request at a time")
    print("ROUTER/DEALER allows concurrent independent message flows")
    print("\nChoose based on your requirements:")
    print("- REP/REQ: Simple request-reply, auto message ordering")
    print("- ROUTER/DEALER: True async, concurrent messages, manual identity handling")


if __name__ == "__main__":
    main()
