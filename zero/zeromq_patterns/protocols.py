from typing import Any, Callable, Optional, Protocol, runtime_checkable

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

    def send_multipart(self, message: list) -> None:
        ...

    def poll(self, timeout: int) -> bool:
        ...

    def recv(self) -> bytes:
        ...

    def recv_multipart(self) -> list:
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

    async def send_multipart(self, message: list) -> None:
        ...

    async def poll(self, timeout: int) -> bool:
        ...

    async def recv(self) -> bytes:
        ...

    async def recv_multipart(self) -> list:
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
    def listen(
        self, address: str, msg_handler: Callable[[bytes, bytes], Optional[bytes]]
    ) -> None:
        ...

    def close(self) -> None:
        ...
