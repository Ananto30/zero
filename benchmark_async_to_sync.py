"""
Benchmark comparing different ways to handle sync/async in RPC worker:
1. Pure sync (blocking socket, sync functions)
2. Pure async (zmq.asyncio, async functions)
3. Hybrid sync + async_to_sync (sync socket, async functions via background event loop)
"""

import asyncio
import logging
import multiprocessing
import threading
import time
from functools import wraps

import zmq
import zmq.asyncio

logging.basicConfig(level=logging.WARNING)

PORT_PURE_SYNC = 5556
PORT_PURE_ASYNC = 5557
PORT_SYNC_WITH_ASYNC_TO_SYNC = 5558
HOST = "127.0.0.1"


# ============================================================================
# async_to_sync implementation (background event loop)
# ============================================================================
_LOOP = None
_THRD = None


def start_async_loop():
    global _LOOP, _THRD
    if _LOOP is None or _THRD is None or not _THRD.is_alive():
        _LOOP = asyncio.new_event_loop()
        _THRD = threading.Thread(target=_LOOP.run_forever, name="Async Runner", daemon=True)
        _THRD.start()


def async_to_sync(func):
    @wraps(func)
    def run(*args, **kwargs):
        start_async_loop()
        try:
            future = asyncio.run_coroutine_threadsafe(func(*args, **kwargs), _LOOP)
            return future.result()
        except Exception as exc:
            raise

    return run


# ============================================================================
# Test async function (simulates RPC work)
# ============================================================================
async def async_work():
    """Simulate some async work"""
    await asyncio.sleep(0.0001)  # Small async operation
    return b"async_result"


# ============================================================================
# APPROACH 1: Pure Sync (sync socket + sync functions)
# ============================================================================
def pure_sync_server():
    """Blocking sync socket, sync functions only"""
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind(f"tcp://{HOST}:{PORT_PURE_SYNC}")
    print("[PURE_SYNC] Server started")

    count = 0
    try:
        while True:
            message = socket.recv()
            # Sync only - no async functions
            socket.send(message)
            count += 1
            if count % 2000 == 0:
                print(f"[PURE_SYNC] Server: {count} requests")
    except KeyboardInterrupt:
        pass
    finally:
        socket.close()
        context.term()


# ============================================================================
# APPROACH 2: Pure Async (zmq.asyncio + async functions)
# ============================================================================
async def pure_async_server():
    """Async socket with async functions"""
    context = zmq.asyncio.Context()
    socket = context.socket(zmq.REP)
    socket.bind(f"tcp://{HOST}:{PORT_PURE_ASYNC}")
    print("[PURE_ASYNC] Server started")

    count = 0
    try:
        while True:
            message = await socket.recv()
            # Call async function
            result = await async_work()
            await socket.send(result)
            count += 1
            if count % 2000 == 0:
                print(f"[PURE_ASYNC] Server: {count} requests")
    except KeyboardInterrupt:
        pass
    finally:
        socket.close()
        context.term()


def pure_async_server_process():
    asyncio.run(pure_async_server())


# ============================================================================
# APPROACH 3: Sync Socket + async_to_sync (for async functions)
# ============================================================================
def sync_with_async_to_sync_server():
    """Sync socket with async functions converted via async_to_sync"""
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind(f"tcp://{HOST}:{PORT_SYNC_WITH_ASYNC_TO_SYNC}")
    print("[SYNC_ASYNC_TO_SYNC] Server started")

    # Convert async function to sync using background event loop
    sync_async_work = async_to_sync(async_work)

    count = 0
    try:
        while True:
            message = socket.recv()
            # Call async function via background event loop
            result = sync_async_work()
            socket.send(result)
            count += 1
            if count % 2000 == 0:
                print(f"[SYNC_ASYNC_TO_SYNC] Server: {count} requests")
    except KeyboardInterrupt:
        pass
    finally:
        socket.close()
        context.term()


# CLIENT
# ============================================================================
def client_benchmark(port: int, label: str, num_requests: int = 10000) -> float:
    """Run benchmark against a server"""
    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    socket.setsockopt(zmq.RCVTIMEO, 5000)
    socket.connect(f"tcp://{HOST}:{port}")

    time.sleep(0.2)

    start = time.time()

    for i in range(num_requests):
        try:
            socket.send(b"test")
            response = socket.recv()
        except zmq.error.Again:
            print(f"{label} timeout after {i} requests")
            break

    elapsed = time.time() - start
    rps = num_requests / elapsed

    socket.close()
    context.term()

    return rps


# ============================================================================
# MAIN
# ============================================================================
if __name__ == "__main__":
    num_requests = 10000

    benchmarks = [
        ("PURE_SYNC", PORT_PURE_SYNC, pure_sync_server, None),
        ("PURE_ASYNC", PORT_PURE_ASYNC, None, pure_async_server_process),
        (
            "SYNC + async_to_sync",
            PORT_SYNC_WITH_ASYNC_TO_SYNC,
            sync_with_async_to_sync_server,
            None,
        ),
    ]

    results = {}

    for name, port, sync_target, async_target in benchmarks:
        print(f"\n{'='*60}")
        print(f"{name.upper()} BENCHMARK: {num_requests} requests")
        print(f"{'='*60}")

        if sync_target:
            server_proc = multiprocessing.Process(target=sync_target)
        else:
            server_proc = multiprocessing.Process(target=async_target)

        server_proc.daemon = True
        server_proc.start()

        time.sleep(0.5)

        rps = client_benchmark(port, name, num_requests)
        results[name] = rps
        print(f"{name} RPS: {rps:.2f} req/sec\n")

        server_proc.terminate()
        server_proc.join(timeout=2)

        time.sleep(1)

    print(f"\n{'='*60}")
    print(f"RESULTS SUMMARY")
    print(f"{'='*60}")

    max_rps = max(results.values())
    for name, rps in results.items():
        ratio = rps / max_rps
        print(f"{name:30s}: {rps:10.2f} req/sec  ({ratio:.2f}x)")

    print(f"{'='*60}\n")
