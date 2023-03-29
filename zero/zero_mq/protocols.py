from typing import Any, Callable, Optional, Protocol

import zmq


class ZeroMQClient(Protocol):  # pragma: no cover
    @property
    def context(self) -> zmq.Context:
        ...

    def connect(self, address: str) -> None:
        ...

    def close(self) -> None:
        ...

    def send(self, message: bytes) -> None:
        ...

    def poll(self, timeout: int) -> bool:
        ...

    def recv(self) -> bytes:
        ...

    def request(self, message: bytes) -> Any:
        ...


class AsyncZeroMQClient(Protocol):  # pragma: no cover
    @property
    def context(self) -> zmq.Context:
        ...

    def connect(self, address: str) -> None:
        ...

    def close(self) -> None:
        ...

    async def send(self, message: bytes) -> None:
        ...

    async def poll(self, timeout: int) -> bool:
        ...

    async def recv(self) -> bytes:
        ...

    async def request(self, message: bytes) -> Any:
        ...


class ZeroMQBroker(Protocol):  # pragma: no cover
    def listen(self, address: str, channel: str) -> None:
        ...

    def close(self) -> None:
        ...


class ZeroMQWorker(Protocol):  # pragma: no cover
    def listen(self, address: str, msg_handler: Callable[[bytes], Optional[bytes]]) -> None:
        ...

    def close(self) -> None:
        ...
