"""
Hybrid approach: asyncio with sync zmq via asyncio.to_thread()
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
PORT_HYBRID = 5558
HOST = "127.0.0.1"


# ============================================================================
# SYNC VERSION
# ============================================================================
def sync_server():
    """Simple sync echo server"""
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind(f"tcp://{HOST}:{PORT_SYNC}")
    print("[SYNC] Server started")

    count = 0
    try:
        while True:
            message = socket.recv()
            socket.send(message)
            count += 1
            if count % 2000 == 0:
                print(f"[SYNC] Server: {count} requests")
    except KeyboardInterrupt:
        pass
    finally:
        socket.close()
        context.term()


# ============================================================================
# ASYNC VERSION (zmq.asyncio)
# ============================================================================
async def async_server():
    """Simple async echo server with zmq.asyncio"""
    context = zmq.asyncio.Context()
    socket = context.socket(zmq.REP)
    socket.bind(f"tcp://{HOST}:{PORT_ASYNC}")
    print("[ASYNC] Server started")

    count = 0
    try:
        while True:
            message = await socket.recv()
            await socket.send(message)
            count += 1
            if count % 2000 == 0:
                print(f"[ASYNC] Server: {count} requests")
    except KeyboardInterrupt:
        pass
    finally:
        socket.close()
        context.term()


def async_server_process():
    asyncio.run(async_server())


# ============================================================================
# HYBRID VERSION: asyncio + sync zmq via asyncio.to_thread()
# ============================================================================
async def hybrid_server():
    """Hybrid: asyncio event loop with sync zmq in thread pool"""
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind(f"tcp://{HOST}:{PORT_HYBRID}")
    print("[HYBRID] Server started")

    count = 0
    try:
        while True:
            # Run blocking zmq recv in thread pool (non-blocking for event loop)
            message = await asyncio.to_thread(socket.recv)

            # Run blocking zmq send in thread pool
            await asyncio.to_thread(socket.send, message)

            count += 1
            if count % 2000 == 0:
                print(f"[HYBRID] Server: {count} requests")
    except KeyboardInterrupt:
        pass
    finally:
        socket.close()
        context.term()


def hybrid_server_process():
    asyncio.run(hybrid_server())


# ============================================================================
# CLIENT (same for all)
# ============================================================================
def client_benchmark(port: int, label: str, num_requests: int = 10000) -> float:
    """Run benchmark against a server"""
    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    socket.setsockopt(zmq.RCVTIMEO, 5000)
    socket.connect(f"tcp://{HOST}:{port}")

    time.sleep(0.2)  # Wait for server to be ready

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

    print(f"\n{'='*60}")
    print(f"SYNC SERVER BENCHMARK: {num_requests} requests")
    print(f"{'='*60}")

    # Start sync server
    sync_server_proc = multiprocessing.Process(target=sync_server)
    sync_server_proc.daemon = True
    sync_server_proc.start()

    time.sleep(0.5)

    # Run sync client benchmark
    sync_rps = client_benchmark(PORT_SYNC, "SYNC", num_requests)
    print(f"Sync RPS: {sync_rps:.2f} req/sec\n")

    sync_server_proc.terminate()
    sync_server_proc.join(timeout=2)

    time.sleep(2)

    print(f"\n{'='*60}")
    print(f"ASYNC SERVER BENCHMARK: {num_requests} requests")
    print(f"{'='*60}")

    # Start async server
    async_server_proc = multiprocessing.Process(target=async_server_process)
    async_server_proc.daemon = True
    async_server_proc.start()

    time.sleep(0.5)

    # Run async client benchmark
    async_rps = client_benchmark(PORT_ASYNC, "ASYNC", num_requests)
    print(f"Async RPS: {async_rps:.2f} req/sec\n")

    async_server_proc.terminate()
    async_server_proc.join(timeout=2)

    time.sleep(2)

    print(f"\n{'='*60}")
    print(f"HYBRID SERVER BENCHMARK: {num_requests} requests")
    print(f"(asyncio + sync zmq via asyncio.to_thread())")
    print(f"{'='*60}")

    # Start hybrid server
    hybrid_server_proc = multiprocessing.Process(target=hybrid_server_process)
    hybrid_server_proc.daemon = True
    hybrid_server_proc.start()

    time.sleep(0.5)

    # Run hybrid client benchmark
    hybrid_rps = client_benchmark(PORT_HYBRID, "HYBRID", num_requests)
    print(f"Hybrid RPS: {hybrid_rps:.2f} req/sec\n")

    hybrid_server_proc.terminate()
    hybrid_server_proc.join(timeout=2)

    print(f"\n{'='*60}")
    print(f"RESULTS")
    print(f"{'='*60}")
    print(f"Sync:   {sync_rps:.2f} req/sec")
    print(f"Async:  {async_rps:.2f} req/sec  ({async_rps/sync_rps:.2f}x)")
    print(f"Hybrid: {hybrid_rps:.2f} req/sec  ({hybrid_rps/sync_rps:.2f}x)")
    print(f"{'='*60}\n")
