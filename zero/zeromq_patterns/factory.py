from zero.zeromq_patterns import queue_device

from .interfaces import AsyncZeroMQClient, ZeroMQBroker, ZeroMQClient, ZeroMQWorker


def get_client(pattern: str, default_timeout: int = 2000) -> ZeroMQClient:
    if pattern == "proxy":
        return queue_device.ZeroMQClient(default_timeout)

    raise ValueError(f"Invalid pattern: {pattern}")


def get_async_client(pattern: str, default_timeout: int) -> AsyncZeroMQClient:
    if pattern == "proxy":
        return queue_device.AsyncZeroMQClient(default_timeout)

    raise ValueError(f"Invalid pattern: {pattern}")


def get_broker(pattern: str) -> ZeroMQBroker:
    if pattern == "proxy":
        return queue_device.ZeroMQBroker()

    raise ValueError(f"Invalid pattern: {pattern}")


def get_worker(pattern: str, worker_id: int) -> ZeroMQWorker:
    if pattern == "proxy":
        return queue_device.ZeroMQWorker(worker_id)

    raise ValueError(f"Invalid pattern: {pattern}")
