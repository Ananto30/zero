"""
Benchmark truly concurrent async using queue pattern - decouple recv from send.
"""

import asyncio
import logging
import multiprocessing
import time

import zmq
import zmq.asyncio

logging.basicConfig(level=logging.WARNING)

PORT_SYNC = 5556
PORT_ASYNC_SEQUENTIAL = 5557
PORT_ASYNC_QUEUE = 5558
HOST = "127.0.0.1"
NUM_CLIENTS = 10


# ============================================================================
# SYNC VERSION
# ============================================================================
def sync_server():
    """Sync echo server - sequential"""
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
            if count % 500 == 0:
                print(f"[SYNC] Server: {count} requests")
    except KeyboardInterrupt:
        pass
    finally:
        socket.close()
        context.term()


# ============================================================================
# ASYNC SEQUENTIAL (old way)
# ============================================================================
async def async_server_sequential():
    """Async sequential - waits for send to complete before next recv"""
    context = zmq.asyncio.Context()
    socket = context.socket(zmq.REP)
    socket.bind(f"tcp://{HOST}:{PORT_ASYNC_SEQUENTIAL}")
    print("[ASYNC-SEQ] Server started")

    count = 0
    try:
        while True:
            message = await socket.recv()
            await socket.send(message)
            count += 1
            if count % 500 == 0:
                print(f"[ASYNC-SEQ] Server: {count} requests")
    except KeyboardInterrupt:
        pass
    finally:
        socket.close()
        context.term()


# ============================================================================
# ASYNC WITH QUEUE (truly concurrent receiver and sender)
# ============================================================================
async def receiver(socket, queue):
    """Continuously receive messages and put in queue"""
    try:
        while True:
            message = await socket.recv()
            await queue.put(message)
    except KeyboardInterrupt:
        pass


async def sender(socket, queue):
    """Continuously send messages from queue"""
    try:
        while True:
            message = await queue.get()
            await socket.send(message)
    except KeyboardInterrupt:
        pass


async def async_server_queue():
    """Queue-based async - receiver and sender run concurrently"""
    context = zmq.asyncio.Context()
    socket = context.socket(zmq.REP)
    socket.bind(f"tcp://{HOST}:{PORT_ASYNC_QUEUE}")
    print("[ASYNC-QUEUE] Server started")

    queue = asyncio.Queue()

    # Create counter task to track progress
    async def counter():
        count = 0
        try:
            while True:
                await queue.get()
                count += 1
                if count % 500 == 0:
                    print(f"[ASYNC-QUEUE] Server: {count} requests")
                # Put it back for sender to process
                await queue.put((await queue.get()))
        except KeyboardInterrupt:
            pass

    # Simpler: just run both receiver and sender
    try:
        await asyncio.gather(receiver(socket, queue), sender(socket, queue))
    except KeyboardInterrupt:
        pass
    finally:
        socket.close()
        context.term()


# Better version with proper counting
async def async_server_queue_v2():
    """Queue-based async with proper counting"""
    context = zmq.asyncio.Context()
    socket = context.socket(zmq.REP)
    socket.bind(f"tcp://{HOST}:{PORT_ASYNC_QUEUE}")
    print("[ASYNC-QUEUE] Server started")

    queue = asyncio.Queue()
    count = 0

    async def receiver_task():
        try:
            while True:
                message = await socket.recv()
                await queue.put(message)
        except:
            pass

    async def sender_task():
        nonlocal count
        try:
            while True:
                message = await queue.get()
                await socket.send(message)
                count += 1
                if count % 500 == 0:
                    print(f"[ASYNC-QUEUE] Server: {count} requests")
        except:
            pass

    try:
        await asyncio.gather(receiver_task(), sender_task())
    except KeyboardInterrupt:
        pass
    finally:
        socket.close()
        context.term()


def async_server_sequential_process():
    asyncio.run(async_server_sequential())


def async_server_queue_process():
    asyncio.run(async_server_queue_v2())


# ============================================================================
# CONCURRENT CLIENT
# ============================================================================
def client_worker(port: int, client_id: int, num_requests: int = 1000):
    """Single client sending requests"""
    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    socket.setsockopt(zmq.RCVTIMEO, 5000)
    socket.connect(f"tcp://{HOST}:{port}")

    for i in range(num_requests):
        try:
            socket.send(b"test")
            response = socket.recv()
        except zmq.error.Again:
            print(f"Client {client_id} timeout after {i} requests")
            break

    socket.close()
    context.term()


def run_concurrent_benchmark(port: int, num_clients: int, num_requests_per_client: int):
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
    print(f"{'='*60}")

    sync_server_proc = multiprocessing.Process(target=sync_server)
    sync_server_proc.daemon = True
    sync_server_proc.start()

    time.sleep(0.5)

    sync_rps, sync_time = run_concurrent_benchmark(PORT_SYNC, num_clients, num_requests_per_client)
    print(f"Sync RPS: {sync_rps:.2f} req/sec")
    print(f"Total time: {sync_time:.2f}s\n")

    sync_server_proc.terminate()
    sync_server_proc.join(timeout=2)

    time.sleep(2)

    print(f"\n{'='*60}")
    print(
        f"ASYNC SEQUENTIAL BENCHMARK: {num_clients} clients, {num_requests_per_client} req/client"
    )
    print(f"{'='*60}")

    async_seq_proc = multiprocessing.Process(target=async_server_sequential_process)
    async_seq_proc.daemon = True
    async_seq_proc.start()

    time.sleep(0.5)

    async_seq_rps, async_seq_time = run_concurrent_benchmark(
        PORT_ASYNC_SEQUENTIAL, num_clients, num_requests_per_client
    )
    print(f"Async Sequential RPS: {async_seq_rps:.2f} req/sec")
    print(f"Total time: {async_seq_time:.2f}s\n")

    async_seq_proc.terminate()
    async_seq_proc.join(timeout=2)

    time.sleep(2)

    print(f"\n{'='*60}")
    print(f"ASYNC QUEUE BENCHMARK: {num_clients} clients, {num_requests_per_client} req/client")
    print(f"(Receiver and Sender run concurrently)")
    print(f"{'='*60}")

    async_queue_proc = multiprocessing.Process(target=async_server_queue_process)
    async_queue_proc.daemon = True
    async_queue_proc.start()

    time.sleep(0.5)

    async_queue_rps, async_queue_time = run_concurrent_benchmark(
        PORT_ASYNC_QUEUE, num_clients, num_requests_per_client
    )
    print(f"Async Queue RPS: {async_queue_rps:.2f} req/sec")
    print(f"Total time: {async_queue_time:.2f}s\n")

    async_queue_proc.terminate()
    async_queue_proc.join(timeout=2)

    print(f"\n{'='*60}")
    print(f"RESULTS")
    print(f"{'='*60}")
    print(f"Sync (Sequential):        {sync_rps:.2f} req/sec  ({sync_time:.2f}s)")
    print(f"Async (Sequential):       {async_seq_rps:.2f} req/sec  ({async_seq_time:.2f}s)")
    print(f"Async (Queue Pattern):    {async_queue_rps:.2f} req/sec  ({async_queue_time:.2f}s)")
    print(f"\nComparisons:")
    print(f"Async Queue vs Sync:           {async_queue_rps / sync_rps:.2f}x")
    print(f"Async Queue vs Async Seq:      {async_queue_rps / async_seq_rps:.2f}x")
    print(f"Time: Async Seq vs Async Queue: {async_seq_time:.2f}s vs {async_queue_time:.2f}s")
    print(f"{'='*60}\n")
