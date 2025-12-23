"""
Benchmark with multiple concurrent clients to show where async truly shines.
"""

import asyncio
import logging
import multiprocessing
import time

import zmq
import zmq.asyncio

logging.basicConfig(level=logging.WARNING)

PORT_SYNC = 5556
PORT_ASYNC = 5557
HOST = "127.0.0.1"
NUM_CLIENTS = 10  # Multiple concurrent clients


# ============================================================================
# SYNC VERSION (can handle one request at a time)
# ============================================================================
def sync_server():
    """Sync echo server - handles clients sequentially"""
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind(f"tcp://{HOST}:{PORT_SYNC}")
    print("[SYNC] Server started")

    count = 0
    try:
        while True:
            message = socket.recv()  # BLOCKS until one client sends
            socket.send(message)  # BLOCKS until one client receives
            count += 1
            if count % 500 == 0:
                print(f"[SYNC] Server: {count} requests")
    except KeyboardInterrupt:
        pass
    finally:
        socket.close()
        context.term()


# ============================================================================
# ASYNC VERSION (can suspend for all clients, interleave requests)
# ============================================================================
async def async_server():
    """Async echo server - suspends for each client, can interleave"""
    context = zmq.asyncio.Context()
    socket = context.socket(zmq.REP)
    socket.bind(f"tcp://{HOST}:{PORT_ASYNC}")
    print("[ASYNC] Server started")

    count = 0
    try:
        while True:
            message = await socket.recv()  # SUSPENDS, event loop can work on other clients
            await socket.send(message)  # SUSPENDS, event loop can work on other clients
            count += 1
            if count % 500 == 0:
                print(f"[ASYNC] Server: {count} requests")
    except KeyboardInterrupt:
        pass
    finally:
        socket.close()
        context.term()


def async_server_process():
    asyncio.run(async_server())


# ============================================================================
# CONCURRENT CLIENT (simulates multiple clients)
# ============================================================================
def client_worker(port: int, client_id: int, num_requests: int = 1000):
    """Single client sending requests"""
    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    socket.setsockopt(zmq.RCVTIMEO, 5000)
    socket.connect(f"tcp://{HOST}:{port}")

    start = time.time()

    for i in range(num_requests):
        try:
            socket.send(b"test")
            response = socket.recv()
        except zmq.error.Again:
            print(f"Client {client_id} timeout after {i} requests")
            break

    elapsed = time.time() - start

    socket.close()
    context.term()

    return elapsed


def run_concurrent_benchmark(port: int, label: str, num_clients: int, num_requests_per_client: int):
    """Run multiple clients concurrently"""
    procs = []

    start = time.time()

    for i in range(num_clients):
        proc = multiprocessing.Process(
            target=client_worker, args=(port, i, num_requests_per_client)
        )
        proc.start()
        procs.append(proc)

    for proc in procs:
        proc.join()

    elapsed = time.time() - start
    total_requests = num_clients * num_requests_per_client
    rps = total_requests / elapsed

    return rps, elapsed


# ============================================================================
# MAIN
# ============================================================================
if __name__ == "__main__":
    num_clients = NUM_CLIENTS
    num_requests_per_client = 1000
    total_requests = num_clients * num_requests_per_client

    print(f"\n{'='*60}")
    print(f"SYNC SERVER BENCHMARK: {num_clients} clients, {num_requests_per_client} req/client")
    print(f"Total: {total_requests} requests")
    print(f"{'='*60}")

    sync_server_proc = multiprocessing.Process(target=sync_server)
    sync_server_proc.daemon = True
    sync_server_proc.start()

    time.sleep(0.5)

    sync_rps, sync_time = run_concurrent_benchmark(
        PORT_SYNC, "SYNC", num_clients, num_requests_per_client
    )
    print(f"Sync RPS: {sync_rps:.2f} req/sec")
    print(f"Total time: {sync_time:.2f}s\n")

    sync_server_proc.terminate()
    sync_server_proc.join(timeout=2)

    time.sleep(2)

    print(f"\n{'='*60}")
    print(f"ASYNC SERVER BENCHMARK: {num_clients} clients, {num_requests_per_client} req/client")
    print(f"Total: {total_requests} requests")
    print(f"{'='*60}")

    async_server_proc = multiprocessing.Process(target=async_server_process)
    async_server_proc.daemon = True
    async_server_proc.start()

    time.sleep(0.5)

    async_rps, async_time = run_concurrent_benchmark(
        PORT_ASYNC, "ASYNC", num_clients, num_requests_per_client
    )
    print(f"Async RPS: {async_rps:.2f} req/sec")
    print(f"Total time: {async_time:.2f}s\n")

    async_server_proc.terminate()
    async_server_proc.join(timeout=2)

    print(f"\n{'='*60}")
    print(f"RESULTS - Multiple Concurrent Clients")
    print(f"{'='*60}")
    print(f"Sync:  {sync_rps:.2f} req/sec  ({sync_time:.2f}s total)")
    print(f"Async: {async_rps:.2f} req/sec  ({async_time:.2f}s total)")
    print(f"\nAsync speedup: {async_rps / sync_rps:.2f}x faster")
    print(f"Time saved: {sync_time - async_time:.2f}s")
    print(f"{'='*60}\n")
