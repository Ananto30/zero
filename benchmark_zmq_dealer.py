#!/usr/bin/env python3
"""
Benchmark comparing REP vs DEALER socket patterns for ZMQ.

REP: Sequential request-reply (one request at a time)
DEALER: Asynchronous socket (can handle multiple concurrent messages)
"""
import asyncio
import multiprocessing
import sys
import time
from typing import Callable

import zmq
import zmq.asyncio


def sync_rep_server(port: int, num_requests: int):
    """Sync REP server - handles one request at a time sequentially."""
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind(f"tcp://127.0.0.1:{port}")

    for i in range(num_requests):
        request = socket.recv()
        # Simulate some work
        time.sleep(0.0001)
        socket.send(b"OK")

    socket.close()
    context.term()


def sync_dealer_server(port: int, num_requests: int):
    """Sync DEALER server - can receive from multiple clients."""
    context = zmq.Context()
    socket = context.socket(zmq.DEALER)
    socket.bind(f"tcp://127.0.0.1:{port}")

    poller = zmq.Poller()
    poller.register(socket, zmq.POLLIN)

    received = 0
    while received < num_requests:
        events = dict(poller.poll(1000))  # 1 second timeout
        if socket in events:
            # DEALER format: [empty frame, message]
            frames = socket.recv_multipart()
            received += 1
            # Simulate some work
            time.sleep(0.0001)
            # Send back to client
            socket.send_multipart(frames[:-1] + [b"OK"])

    socket.close()
    context.term()


async def async_rep_server(port: int, num_requests: int):
    """Async REP server - sequential request-reply."""
    context = zmq.asyncio.Context()
    socket = context.socket(zmq.REP)
    socket.bind(f"tcp://127.0.0.1:{port}")

    for i in range(num_requests):
        request = await socket.recv()
        # Simulate some work
        await asyncio.sleep(0.0001)
        await socket.send(b"OK")

    socket.close()


async def async_dealer_server(port: int, num_requests: int):
    """Async DEALER server - concurrent message handling."""
    context = zmq.asyncio.Context()
    socket = context.socket(zmq.DEALER)
    socket.bind(f"tcp://127.0.0.1:{port}")

    async def process_messages():
        """Continuously receive and process messages concurrently."""
        received = 0
        while received < num_requests:
            try:
                # DEALER format: [empty frame, message]
                frames = await socket.recv_multipart(zmq.NOBLOCK)
                received += 1
                # Simulate some work
                await asyncio.sleep(0.0001)
                # Send back to client (DEALER requires echo of identity frames)
                socket.send_multipart(frames[:-1] + [b"OK"], zmq.NOBLOCK)
            except zmq.Again:
                await asyncio.sleep(0.001)

    await process_messages()
    socket.close()


async def async_dealer_server_with_poller(port: int, num_requests: int):
    """Async DEALER server using zmq.asyncio.Poller for cleaner async handling."""
    context = zmq.asyncio.Context()
    socket = context.socket(zmq.DEALER)
    socket.bind(f"tcp://127.0.0.1:{port}")

    poller = zmq.asyncio.Poller()
    poller.register(socket, zmq.POLLIN)

    received = 0
    while received < num_requests:
        events = await poller.poll(1000)
        event_dict = dict(events)
        if socket in event_dict:
            # DEALER format: [empty frame, message]
            frames = await socket.recv_multipart()
            received += 1
            # Simulate some work
            await asyncio.sleep(0.0001)
            # Send back to client
            await socket.send_multipart(frames[:-1] + [b"OK"])

    socket.close()


def client_worker(port: int, num_requests: int, socket_type: str = "REQ"):
    """Client worker process - sends requests and receives responses."""
    context = zmq.Context()

    if socket_type == "DEALER":
        socket = context.socket(zmq.DEALER)
    elif socket_type == "REQ":
        socket = context.socket(zmq.REQ)
    else:
        raise ValueError(f"Unknown socket type: {socket_type}")

    socket.connect(f"tcp://127.0.0.1:{port}")

    for i in range(num_requests):
        if socket_type == "DEALER":
            socket.send(b"REQUEST")
            response = socket.recv()
        else:
            socket.send(b"REQUEST")
            response = socket.recv()

    socket.close()
    context.term()


def run_benchmark(
    server_func: Callable,
    port: int,
    num_clients: int,
    requests_per_client: int,
    name: str,
    socket_type: str = "REQ",
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
                    asyncio.to_thread(client_worker, port, requests_per_client, socket_type)
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
            multiprocessing.Process(
                target=client_worker, args=(port, requests_per_client, socket_type)
            )
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

    # Test 1: Sync REP (baseline)
    rps, t = run_benchmark(
        sync_rep_server,
        5555,
        num_clients,
        requests_per_client,
        "SYNC REP SERVER (Sequential)",
        socket_type="REQ",
    )
    results["Sync REP"] = (rps, t)

    # Test 2: Sync DEALER with polling
    rps, t = run_benchmark(
        sync_dealer_server,
        5556,
        num_clients,
        requests_per_client,
        "SYNC DEALER SERVER (Polling)",
        socket_type="DEALER",
    )
    results["Sync DEALER"] = (rps, t)

    # Test 3: Async REP
    rps, t = run_benchmark(
        async_rep_server,
        5557,
        num_clients,
        requests_per_client,
        "ASYNC REP SERVER (Sequential)",
        socket_type="REQ",
    )
    results["Async REP"] = (rps, t)

    # Test 4: Async DEALER (non-blocking approach)
    rps, t = run_benchmark(
        async_dealer_server,
        5558,
        num_clients,
        requests_per_client,
        "ASYNC DEALER SERVER (Non-blocking)",
        socket_type="DEALER",
    )
    results["Async DEALER (non-blocking)"] = (rps, t)

    # Test 5: Async DEALER with Poller
    rps, t = run_benchmark(
        async_dealer_server_with_poller,
        5559,
        num_clients,
        requests_per_client,
        "ASYNC DEALER SERVER (Poller)",
        socket_type="DEALER",
    )
    results["Async DEALER (poller)"] = (rps, t)

    # Print summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")

    max_rps = max(rps for rps, _ in results.values())

    for name, (rps, elapsed) in results.items():
        ratio = rps / max_rps if max_rps > 0 else 0
        print(f"{name:35} {rps:>12,.0f} RPS  {elapsed:>6.3f}s  ({ratio:.2f}x)")

    print(f"\nFastest: {max(results.items(), key=lambda x: x[1][0])[0]}")


if __name__ == "__main__":
    main()
