# Async/Await

Zero has full support for async operations, perfect for building high-concurrency services.

## Async Server

Create async RPC methods in your server:

```python
import asyncio
from zero import ZeroServer

app = ZeroServer(port=5559)

@app.register_rpc
async def fetch_data(url: str) -> str:
    """Simulate async I/O operation"""
    await asyncio.sleep(1)  # Simulate network call
    return f"Data from {url}"

@app.register_rpc
async def process_task(task_id: int) -> bool:
    """Process a task asynchronously"""
    await asyncio.sleep(0.5)
    return True

@app.register_rpc
def sync_operation(text: str) -> str:
    """Mix sync and async methods"""
    return text.upper()

if __name__ == "__main__":
    app.run()
```

## Async Client (Synchronous)

Even with async server methods, you can call them synchronously:

```python
from zero import ZeroClient

client = ZeroClient("localhost", 5559)

# Calls to async server methods
result1 = client.call("fetch_data", "https://api.example.com")
result2 = client.call("process_task", 123)

print(result1)
print(result2)
```

## AsyncZeroClient

For async client code, use `AsyncZeroClient`:

```python
import asyncio
from zero import AsyncZeroClient

async def main():
    client = AsyncZeroClient("localhost", 5559)

    # Await async calls
    result1 = await client.call("fetch_data", "https://api.example.com")
    result2 = await client.call("process_task", 123)

    print(result1)
    print(result2)

if __name__ == "__main__":
    asyncio.run(main())
```

## Concurrent Requests

Make multiple concurrent requests with async client:

```python
import asyncio
from zero import AsyncZeroClient

async def main():
    client = AsyncZeroClient("localhost", 5559)

    # Run multiple requests concurrently
    results = await asyncio.gather(
        client.call("fetch_data", "https://api1.example.com"),
        client.call("fetch_data", "https://api2.example.com"),
        client.call("fetch_data", "https://api3.example.com"),
    )

    for i, result in enumerate(results, 1):
        print(f"Request {i}: {result}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Real-World Example: API Gateway

### Server with Async Operations

```python
import asyncio
from zero import ZeroServer
from dataclasses import dataclass

app = ZeroServer(port=5559)

@dataclass
class User:
    id: int
    name: str
    email: str

# Simulate database calls
async def get_user_from_db(user_id: int) -> User:
    await asyncio.sleep(0.1)  # Simulate DB query
    return User(id=user_id, name="John Doe", email="john@example.com")

async def save_user_to_db(user: User) -> bool:
    await asyncio.sleep(0.1)  # Simulate DB write
    return True

@app.register_rpc
async def get_user(user_id: int) -> User:
    return await get_user_from_db(user_id)

@app.register_rpc
async def update_user(user: User) -> bool:
    return await save_user_to_db(user)

if __name__ == "__main__":
    app.run()
```

### Client with Concurrent Calls

```python
import asyncio
from zero import AsyncZeroClient
from server import User

async def main():
    client = AsyncZeroClient("localhost", 5559)

    # Fetch multiple users concurrently
    print("Fetching users...")
    results = await asyncio.gather(
        client.call("get_user", 1, return_type=User),
        client.call("get_user", 2, return_type=User),
        client.call("get_user", 3, return_type=User),
    )

    print(f"Fetched {len(results)} users")
    for user in results:
        print(f"  - {user.name} ({user.email})")

    # Update a user
    user = results[0]
    user.name = "Updated Name"
    updated = await client.call("update_user", user)
    print(f"Update successful: {updated}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Mixing Sync and Async

You can mix sync and async methods in the same server:

```python
from zero import ZeroServer
import asyncio

app = ZeroServer(port=5559)

# Synchronous method
@app.register_rpc
def sync_method(data: str) -> str:
    return data.upper()

# Asynchronous method
@app.register_rpc
async def async_method(data: str) -> str:
    await asyncio.sleep(1)
    return data.lower()

if __name__ == "__main__":
    app.run()
```

## Performance with Async

### Without Async

```python
from zero import ZeroServer
import time

app = ZeroServer(port=5559)

@app.register_rpc
def slow_operation(duration: float) -> str:
    time.sleep(duration)  # Blocks entire worker
    return f"Done in {duration}s"

if __name__ == "__main__":
    app.run()
```

With sync code, long operations block the worker process.

### With Async

```python
import asyncio
from zero import ZeroServer

app = ZeroServer(port=5559)

@app.register_rpc
async def efficient_operation(duration: float) -> str:
    await asyncio.sleep(duration)  # Non-blocking
    return f"Done in {duration}s"

if __name__ == "__main__":
    app.run()
```

With async, the worker can handle other requests while waiting.

## Best Practices

✅ **DO:**

- Use async for I/O-bound operations
- Use `asyncio.gather()` for concurrent requests
- Await all async calls properly
- Use `AsyncZeroClient` for async code

❌ **DON'T:**

- Block the event loop with CPU-intensive work
- Mix sync and async incorrectly

## Next Steps

- [Code Generation](code-generation.md) - Generate async clients
- [TCP Protocol](tcp-protocol.md) - Combine async with TCP
- [Benchmarks](../benchmarks.md) - See async performance
