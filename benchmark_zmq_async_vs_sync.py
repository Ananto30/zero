"""
Simple benchmark comparing zmq sync vs async performance.
"""

import asyncio
import logging
import multiprocessing
import time
from typing import Callable, Optional

import zmq
import zmq.asyncio

logging.basicConfig(level=logging.WARNING)

PORT = 5555
HOST = "127.0.0.1"


# ============================================================================
# SYNC VERSION
# ============================================================================
class SyncWorker:
    def __init__(self, worker_id: int):
        self.worker_id = worker_id
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.DEALER)
        self.socket.setsockopt(zmq.LINGER, 0)
        self.socket.setsockopt(zmq.SNDTIMEO, 2000)

    def listen(self, address: str):
        self.socket.connect(address)
        print(f"[SYNC] Worker {self.worker_id} started")

        count = 0
        while True:
            try:
                frames = self.socket.recv_multipart()
                if len(frames) != 2:
                    continue

                ident, data = frames

                # Simple echo: just send back the data
                self.socket.send_multipart([ident, data])
                count += 1

                if count % 10000 == 0:
                    print(f"[SYNC] Worker {self.worker_id} processed {count} messages")

            except zmq.error.Again:
                continue
            except KeyboardInterrupt:
                break

    def close(self):
        self.socket.close()
        self.context.term()


# ============================================================================
# ASYNC VERSION
# ============================================================================
class AsyncWorker:
    def __init__(self, worker_id: int):
        self.worker_id = worker_id
        self.context = zmq.asyncio.Context()
        self.socket = self.context.socket(zmq.DEALER)
        self.socket.setsockopt(zmq.LINGER, 0)
        self.socket.setsockopt(zmq.SNDTIMEO, 2000)

    async def listen(self, address: str):
        self.socket.connect(address)
        print(f"[ASYNC] Worker {self.worker_id} started")

        count = 0
        while True:
            try:
                frames = await self.socket.recv_multipart()
                if len(frames) != 2:
                    continue

                ident, data = frames

                # Simple echo: just send back the data
                await self.socket.send_multipart([ident, data])
                count += 1

                if count % 10000 == 0:
                    print(f"[ASYNC] Worker {self.worker_id} processed {count} messages")

            except zmq.error.Again:
                await asyncio.sleep(0.01)
            except KeyboardInterrupt:
                break

    def close(self):
        self.socket.close()
        self.context.term()


# ============================================================================
# CLIENT (same for both)
# ============================================================================
class Client:
    def __init__(self, num_requests: int = 100000):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.DEALER)
        self.socket.setsockopt(zmq.RCVTIMEO, 5000)
        self.num_requests = num_requests

    def connect(self, address: str):
        self.socket.connect(address)

    def run(self) -> float:
        """Run benchmark and return RPS"""
        start = time.time()

        for i in range(self.num_requests):
            # Send a request
            self.socket.send(b"test_message")

            try:
                # Wait for response
                response = self.socket.recv()
            except zmq.error.Again:
                print(f"Timeout after {i} requests")
                break

        elapsed = time.time() - start
        rps = self.num_requests / elapsed
        return rps

    def close(self):
        self.socket.close()
        self.context.term()


# ============================================================================
# BROKER (same for both)
# ============================================================================
class Broker:
    def __init__(self, num_workers: int = 4):
        self.context = zmq.Context()
        self.frontend = self.context.socket(zmq.ROUTER)
        self.backend = self.context.socket(zmq.DEALER)
        self.num_workers = num_workers

    def start(self, address: str):
        self.frontend.bind(f"tcp://{HOST}:{PORT}")
        self.backend.bind(f"tcp://{HOST}:{PORT + 1}")
        print(f"[BROKER] Started with {self.num_workers} workers")

        try:
            zmq.device(zmq.QUEUE, self.frontend, self.backend)
        except KeyboardInterrupt:
            pass

    def close(self):
        self.frontend.close()
        self.backend.close()
        self.context.term()


# ============================================================================
# SYNC BENCHMARK
# ============================================================================
def sync_worker_process(worker_id: int):
    """Run a sync worker in a separate process"""
    worker = SyncWorker(worker_id)
    worker.listen(f"tcp://{HOST}:{PORT + 1}")
    worker.close()


def benchmark_sync(num_workers: int = 4, num_requests: int = 100000):
    print(f"\n{'='*60}")
    print(f"SYNC BENCHMARK: {num_workers} workers, {num_requests} requests")
    print(f"{'='*60}")

    # Start broker
    broker = Broker(num_workers)
    broker_proc = multiprocessing.Process(target=broker.start, args=(f"tcp://{HOST}:{PORT}",))
    broker_proc.daemon = True
    broker_proc.start()

    time.sleep(1)

    # Start workers
    worker_procs = []
    for i in range(num_workers):
        proc = multiprocessing.Process(target=sync_worker_process, args=(i,))
        proc.daemon = True
        proc.start()
        worker_procs.append(proc)

    time.sleep(1)

    # Run benchmark
    client = Client(num_requests)
    client.connect(f"tcp://{HOST}:{PORT}")
    rps = client.run()
    client.close()

    # Cleanup
    for proc in worker_procs:
        proc.terminate()
    broker_proc.terminate()

    print(f"Sync RPS: {rps:.2f} req/sec")
    return rps


# ============================================================================
# ASYNC BENCHMARK
# ============================================================================
async def async_worker_task(worker_id: int):
    """Run an async worker"""
    worker = AsyncWorker(worker_id)
    await worker.listen(f"tcp://{HOST}:{PORT + 1}")
    worker.close()


def async_worker_process(worker_id: int):
    """Run an async worker in a separate process"""
    asyncio.run(async_worker_task(worker_id))


def benchmark_async(num_workers: int = 4, num_requests: int = 100000):
    print(f"\n{'='*60}")
    print(f"ASYNC BENCHMARK: {num_workers} workers, {num_requests} requests")
    print(f"{'='*60}")

    # Start broker
    broker = Broker(num_workers)
    broker_proc = multiprocessing.Process(target=broker.start, args=(f"tcp://{HOST}:{PORT}",))
    broker_proc.daemon = True
    broker_proc.start()

    time.sleep(1)

    # Start workers
    worker_procs = []
    for i in range(num_workers):
        proc = multiprocessing.Process(target=async_worker_process, args=(i,))
        proc.daemon = True
        proc.start()
        worker_procs.append(proc)

    time.sleep(1)

    # Run benchmark
    client = Client(num_requests)
    client.connect(f"tcp://{HOST}:{PORT}")
    rps = client.run()
    client.close()

    # Cleanup
    for proc in worker_procs:
        proc.terminate()
    broker_proc.terminate()

    print(f"Async RPS: {rps:.2f} req/sec")
    return rps


# ============================================================================
# MAIN
# ============================================================================
if __name__ == "__main__":
    num_workers = 2
    num_requests = 10000

    sync_rps = benchmark_sync(num_workers, num_requests)
    time.sleep(2)

    async_rps = benchmark_async(num_workers, num_requests)

    print(f"\n{'='*60}")
    print(f"RESULTS")
    print(f"{'='*60}")
    print(f"Sync:  {sync_rps:.2f} req/sec")
    print(f"Async: {async_rps:.2f} req/sec")
    print(f"Ratio: {async_rps / sync_rps:.2f}x (async vs sync)")
    print(f"{'='*60}\n")
