#!/usr/bin/env python3
"""
Benchmark comparing REP/REQ vs ROUTER/DEALER with fully async clients.

This isolates the socket pattern performance without threading overhead.
"""
import asyncio
import time

import zmq
import zmq.asyncio


async def sync_rep_server(port: int, num_requests: int):
    """Sync REP server in separate process (simulated with blocking iteration)."""
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind(f"tcp://127.0.0.1:{port}")

    # Run in thread to avoid blocking event loop
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _run_sync_rep, socket, num_requests)

    socket.close()
    context.term()


def _run_sync_rep(socket, num_requests):
    """Helper to run sync REP server."""
    for i in range(num_requests):
        request = socket.recv()
        time.sleep(0.0001)
        socket.send(b"OK")


async def async_rep_server(port: int, num_requests: int):
    """Async REP server - sequential request-reply."""
    context = zmq.asyncio.Context()
    socket = context.socket(zmq.REP)
    socket.bind(f"tcp://127.0.0.1:{port}")

    for i in range(num_requests):
        request = await socket.recv()
        await asyncio.sleep(0.0001)
        await socket.send(b"OK")

    socket.close()


async def async_router_server(port: int, num_requests: int):
    """Async ROUTER server - concurrent message handling."""
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
            frames = await socket.recv_multipart()
            received += 1
            await asyncio.sleep(0.0001)
            # Send back with identity frame
            await socket.send_multipart([frames[0], b"", b"OK"])

    socket.close()


async def async_req_client(port: int, client_id: int, num_requests: int):
    """Async REQ client."""
    context = zmq.asyncio.Context()
    socket = context.socket(zmq.REQ)
    socket.connect(f"tcp://127.0.0.1:{port}")

    for i in range(num_requests):
        await socket.send(b"REQUEST")
        response = await socket.recv()

    socket.close()


async def async_dealer_client(port: int, client_id: int, num_requests: int):
    """Async DEALER client."""
    context = zmq.asyncio.Context()
    socket = context.socket(zmq.DEALER)
    socket.connect(f"tcp://127.0.0.1:{port}")

    for i in range(num_requests):
        await socket.send(b"REQUEST")
        response = await socket.recv()

    socket.close()


async def run_benchmark(
    server_func,
    client_func,
    port: int,
    num_clients: int,
    requests_per_client: int,
    name: str,
):
    """Run benchmark with async server and async clients."""
    print(f"\n{'='*60}")
    print(f"{name}")
    print(f"{'='*60}")
    print(f"Clients: {num_clients}, Requests/client: {requests_per_client}")

    total_requests = num_clients * requests_per_client

    start_time = time.time()

    # Start server
    server_task = asyncio.create_task(server_func(port, total_requests))

    # Give server time to bind
    await asyncio.sleep(0.5)

    # Start all clients concurrently
    clients = [
        asyncio.create_task(client_func(port, i, requests_per_client)) for i in range(num_clients)
    ]

    # Wait for all clients
    await asyncio.gather(*clients)

    # Wait for server
    await server_task

    elapsed = time.time() - start_time
    rps = total_requests / elapsed if elapsed > 0 else 0

    print(f"Time: {elapsed:.3f}s")
    print(f"RPS: {rps:,.0f} req/sec")

    return rps, elapsed


async def main():
    num_clients = 10
    requests_per_client = 1000

    results = {}

    # Test 1: Async REP/REQ
    rps, t = await run_benchmark(
        async_rep_server,
        async_req_client,
        5555,
        num_clients,
        requests_per_client,
        "ASYNC REP/REQ (Sequential)",
    )
    results["Async REP/REQ"] = (rps, t)

    # Test 2: Async ROUTER/DEALER
    rps, t = await run_benchmark(
        async_router_server,
        async_dealer_client,
        5556,
        num_clients,
        requests_per_client,
        "ASYNC ROUTER/DEALER (Concurrent)",
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

    # Calculate difference
    rep_rps = results["Async REP/REQ"][0]
    router_rps = results["Async ROUTER/DEALER"][0]
    pct_diff = ((router_rps - rep_rps) / rep_rps) * 100

    print(f"\n{'='*60}")
    print("ANALYSIS")
    print(f"{'='*60}")
    print(f"ROUTER/DEALER is {abs(pct_diff):.1f}% {'slower' if pct_diff < 0 else 'faster'}")
    print("\nWhy ROUTER/DEALER might be slower in this benchmark:")
    print("- Requires polling (extra overhead vs blocking recv)")
    print("- Identity frame handling adds per-message overhead")
    print("- No performance benefit without true async work (DB queries, etc)")
    print("\nWhen to use ROUTER/DEALER:")
    print("- When you need true concurrent request handling")
    print("- When you have actual async I/O in your handlers")
    print("- When strict request-reply ordering isn't needed")


if __name__ == "__main__":
    asyncio.run(main())
