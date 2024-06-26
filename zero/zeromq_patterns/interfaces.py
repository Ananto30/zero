from typing import Callable, Optional, Protocol, runtime_checkable


@runtime_checkable
class ZeroMQClient(Protocol):  # pragma: no cover
    def __init__(
        self,
        address: str,
        default_timeout: int = 2000,
    ): ...

    def connect(self, address: str) -> None: ...

    def request(self, message: bytes, timeout: Optional[int] = None) -> bytes: ...

    def close(self) -> None: ...


@runtime_checkable
class AsyncZeroMQClient(Protocol):  # pragma: no cover
    def __init__(
        self,
        address: str,
        default_timeout: int = 2000,
    ): ...

    async def connect(self, address: str) -> None: ...

    async def request(self, message: bytes, timeout: Optional[int] = None) -> bytes: ...

    def close(self) -> None: ...


@runtime_checkable
class ZeroMQBroker(Protocol):  # pragma: no cover
    def listen(self, address: str, channel: str) -> None: ...

    def close(self) -> None: ...


@runtime_checkable
class ZeroMQWorker(Protocol):  # pragma: no cover
    def listen(
        self, address: str, msg_handler: Callable[[bytes, bytes], Optional[bytes]]
    ) -> None: ...

    def close(self) -> None: ...
