"""
Simple benchmark comparing zmq sync vs async performance with blocking and non-blocking.
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
PORT_SYNC_NB = 5558
PORT_ASYNC_NB = 5559
HOST = "127.0.0.1"


# ============================================================================
# SYNC VERSION (BLOCKING)
# ============================================================================
def sync_server():
    """Simple sync echo server (blocking)"""
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
# SYNC VERSION (NON-BLOCKING)
# ============================================================================
def sync_server_nonblocking():
    """Non-blocking sync server with polling"""
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind(f"tcp://{HOST}:{PORT_SYNC_NB}")

    poller = zmq.Poller()
    poller.register(socket, zmq.POLLIN)

    print("[SYNC-NONBLOCKING] Server started")

    count = 0
    try:
        while True:
            events = dict(poller.poll(10))  # Poll with 10ms timeout
            if socket in events:
                try:
                    message = socket.recv(zmq.NOBLOCK)
                    socket.send(message, zmq.NOBLOCK)
                    count += 1
                    if count % 2000 == 0:
                        print(f"[SYNC-NONBLOCKING] Server: {count} requests")
                except zmq.error.Again:
                    pass
    except KeyboardInterrupt:
        pass
    finally:
        socket.close()
        context.term()


# ============================================================================
# ASYNC VERSION (BLOCKING)
# ============================================================================
async def async_server():
    """Async echo server with blocking recv/send"""
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


# ============================================================================
# ASYNC VERSION (EVENT-DRIVEN - truly async, no polling)
# ============================================================================
async def async_server_nonblocking():
    """True event-driven async echo server"""
    context = zmq.asyncio.Context()
    socket = context.socket(zmq.REP)
    socket.bind(f"tcp://{HOST}:{PORT_ASYNC_NB}")

    print("[ASYNC-EVENT-DRIVEN] Server started")

    count = 0
    try:
        while True:
            # Purely event-based - no polling, no spin loop
            # The event loop suspends until data is available
            message = await socket.recv()
            await socket.send(message)
            count += 1
            if count % 2000 == 0:
                print(f"[ASYNC-EVENT-DRIVEN] Server: {count} requests")
        pass
    finally:
        socket.close()
        context.term()


def async_server_process():
    asyncio.run(async_server())


def async_server_nonblocking_process():
    asyncio.run(async_server_nonblocking())


# ============================================================================
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

    print(f"\n{'='*60}")
    print(f"SYNC SERVER (BLOCKING) BENCHMARK: {num_requests} requests")
    print(f"{'='*60}")

    sync_server_proc = multiprocessing.Process(target=sync_server)
    sync_server_proc.daemon = True
    sync_server_proc.start()

    time.sleep(0.5)

    sync_rps = client_benchmark(PORT_SYNC, "SYNC", num_requests)
    print(f"Sync (Blocking) RPS: {sync_rps:.2f} req/sec\n")

    sync_server_proc.terminate()
    sync_server_proc.join(timeout=2)

    time.sleep(2)

    print(f"\n{'='*60}")
    print(f"SYNC SERVER (NON-BLOCKING) BENCHMARK: {num_requests} requests")
    print(f"{'='*60}")

    sync_server_nb_proc = multiprocessing.Process(target=sync_server_nonblocking)
    sync_server_nb_proc.daemon = True
    sync_server_nb_proc.start()

    time.sleep(0.5)

    sync_nb_rps = client_benchmark(PORT_SYNC_NB, "SYNC-NB", num_requests)
    print(f"Sync (Non-blocking) RPS: {sync_nb_rps:.2f} req/sec\n")

    sync_server_nb_proc.terminate()
    sync_server_nb_proc.join(timeout=2)

    time.sleep(2)

    print(f"\n{'='*60}")
    print(f"ASYNC SERVER (BLOCKING) BENCHMARK: {num_requests} requests")
    print(f"{'='*60}")

    async_server_proc = multiprocessing.Process(target=async_server_process)
    async_server_proc.daemon = True
    async_server_proc.start()

    time.sleep(0.5)

    async_rps = client_benchmark(PORT_ASYNC, "ASYNC", num_requests)
    print(f"Async (Blocking) RPS: {async_rps:.2f} req/sec\n")

    async_server_proc.terminate()
    async_server_proc.join(timeout=2)

    time.sleep(2)

    print(f"\n{'='*60}")
    print(f"ASYNC SERVER (EVENT-DRIVEN) BENCHMARK: {num_requests} requests")
    print(f"{'='*60}")

    async_server_nb_proc = multiprocessing.Process(target=async_server_nonblocking_process)
    async_server_nb_proc.daemon = True
    async_server_nb_proc.start()

    time.sleep(0.5)

    async_nb_rps = client_benchmark(PORT_ASYNC_NB, "ASYNC-ED", num_requests)
    print(f"Async (Event-Driven) RPS: {async_nb_rps:.2f} req/sec\n")

    async_server_nb_proc.terminate()
    async_server_nb_proc.join(timeout=2)

    print(f"\n{'='*60}")
    print(f"RESULTS")
    print(f"{'='*60}")
    print(f"Sync (Blocking):        {sync_rps:.2f} req/sec")
    print(f"Sync (Non-blocking):    {sync_nb_rps:.2f} req/sec")
    print(f"Async (Blocking):       {async_rps:.2f} req/sec")
    print(f"Async (Event-Driven):   {async_nb_rps:.2f} req/sec")
    print(f"\nComparisons:")
    print(f"Async (ED) vs Sync (Blocking):   {async_nb_rps / sync_rps:.2f}x")
    print(f"Async (ED) vs Sync (NB):         {async_nb_rps / sync_nb_rps:.2f}x")
    print(f"{'='*60}\n")
