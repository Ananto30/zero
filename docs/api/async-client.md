# AsyncZeroClient API Reference

## Overview

`AsyncZeroClient` is the asynchronous client for calling RPC methods with async/await support.

## Constructor

```python
AsyncZeroClient(
    host: str,
    port: int,
    default_timeout: int = 5000,
    encoder: Type[Encoder] = GenericEncoder,
    protocol: Type[AsyncZeroClientProtocol] = AsyncZMQClient,
    pool_size: int = 50,
)
```

### Parameters

- **host** (str): Server hostname or IP address.
- **port** (int): Server port number.
- **default_timeout** (int): Default timeout for calls in milliseconds. Default: 5000
- **encoder** (Encoder): Message encoder matching server. Default: Msgspec
- **protocol** (AsyncClientProtocol): Async communication protocol. Default: ZeroMQ
    - `zero.protocols.zeromq.AsyncZeroMQClient` - ZeroMQ (default)
    - `zero.protocols.tcp.AsyncTCPClient` - Raw TCP
- **pool_size** (int): Connection pool size for reusing connections. Default: 50

### Example

```python
import asyncio
from zero import AsyncZeroClient
from zero.protocols.tcp import AsyncTCPClient

async def main():
    client = AsyncZeroClient(
        host="192.168.1.100",
        port=5559,
        protocol=AsyncTCPClient
    )

asyncio.run(main())
```

## Methods

### call

Asynchronously call an RPC method on the server.

```python
async def call(
    rpc_func_name: str,
    msg: AllowedType,
    timeout: Optional[int] = None,
    return_type: Optional[Type[T]] = None,
) -> T
```

**Parameters:**

- **rpc_func_name** (str): Name of the RPC method to call
- **msg** (Any): Argument to pass to the method
- **timeout** (int): Timeout for the call in milliseconds. Optional. Defaults to `default_timeout`.
- **return_type** (Type): Expected return type for type conversion. Optional.

**Returns:** Response from the server (awaitable)

**Raises:** Exception if server returns error

## Usage Examples

### Basic Async Call

```python
import asyncio
from zero import AsyncZeroClient

async def main():
    client = AsyncZeroClient("localhost", 5559)
    result = await client.call("hello_world", None)
    print(result)

asyncio.run(main())
```

### Multiple Sequential Calls

```python
import asyncio
from zero import AsyncZeroClient

async def main():
    client = AsyncZeroClient("localhost", 5559)

    result1 = await client.call("method1", "data1")
    result2 = await client.call("method2", result1)
    result3 = await client.call("method3", result2)

    print(result3)

asyncio.run(main())
```

### Concurrent Requests

```python
import asyncio
from zero import AsyncZeroClient

async def main():
    client = AsyncZeroClient("localhost", 5559)

    # Run 10 requests concurrently
    results = await asyncio.gather(
        *[client.call("process", i) for i in range(10)]
    )

    print(f"Completed {len(results)} requests")

asyncio.run(main())
```

### With Type Conversion

```python
import asyncio
from zero import AsyncZeroClient
from dataclasses import dataclass

@dataclass
class User:
    id: int
    name: str
    email: str

async def main():
    client = AsyncZeroClient("localhost", 5559)

    user = await client.call("get_user", 1, return_type=User)
    print(f"User: {user.name} <{user.email}>")

asyncio.run(main())
```

## Protocol Selection

### ZeroMQ (Default)

```python
client = AsyncZeroClient("localhost", 5559)
# Uses ZeroMQ by default
```

### TCP (Better Performance)

```python
from zero.protocols.tcp import AsyncTCPClient

client = AsyncZeroClient(
    "localhost", 5559,
    protocol=AsyncTCPClient
)
```

## Connection Pooling

```python
import asyncio
from zero import AsyncZeroClient

async def main():
    # Single client handles multiple concurrent requests
    client = AsyncZeroClient("localhost", 5559)

    tasks = [
        client.call("method", f"data_{i}")
        for i in range(100)
    ]

    results = await asyncio.gather(*tasks)
    print(f"Completed {len(results)} requests")

asyncio.run(main())
```

## Best Practices

✅ **DO:**

- Use `asyncio.gather()` for concurrent requests
- Reuse client instance across multiple calls
- Use `asyncio.wait_for()` for timeouts
- Handle `asyncio.TimeoutError` and `ConnectionError`
- Use `return_type` for type conversion

❌ **DON'T:**

- Create new client for each call
- Block the event loop with sync operations
- Use sync `ZeroClient` in async code

## Next Steps

- [ZeroClient](client.md) - Synchronous client
- [Guides - Async/Await](../guides/async-await.md) - Detailed async patterns
- [Guides - Code Generation](../guides/code-generation.md) - Generate async clients
