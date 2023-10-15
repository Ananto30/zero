from typing import Any, Awaitable, Callable, Optional, Protocol, runtime_checkable

import zmq
import zmq.asyncio


@runtime_checkable
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


@runtime_checkable
class AsyncZeroMQClient(Protocol):  # pragma: no cover
    @property
    def context(self) -> zmq.asyncio.Context:
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


@runtime_checkable
class ZeroMQBroker(Protocol):  # pragma: no cover
    def listen(self, address: str, channel: str) -> None:
        ...

    def close(self) -> None:
        ...


@runtime_checkable
class ZeroMQWorker(Protocol):  # pragma: no cover
    async def listen(
        self, address: str, msg_handler: Callable[[bytes], Awaitable[Optional[bytes]]]
    ) -> None:
        ...

    def close(self) -> None:
        ...
