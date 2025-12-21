# Code Generation

Zero provides powerful code generation tools to automatically create type-safe clients from your running server!

## Benefits

- 🔒 **Type-safe** - Full type hints in generated code
- 🤖 **Automatic** - Generate from live servers
- 📦 **Schema included** - Data models are auto-generated
- 🔄 **Always in sync** - Never worry about outdated schemas
- 🚀 **Remote servers** - Generate from any server

## Basic Usage

### Step 1: Start Your Server

```python
from zero import ZeroServer
from dataclasses import dataclass

app = ZeroServer(port=5559)

@dataclass
class User:
    id: int
    name: str
    email: str

@app.register_rpc
def get_user(user_id: int) -> User:
    return User(id=user_id, name="John", email="john@example.com")

@app.register_rpc
def save_user(user: User) -> bool:
    return True

if __name__ == "__main__":
    app.run()
```

### Step 2: Generate Client Code

```bash
python -m zero.generate_client \
  --host localhost \
  --port 5559 \
  --protocol zmq \
  --overwrite-dir ./generated_client
```

### Step 3: Use Generated Client

The generated client includes all schemas and type hints:

```python
from generated_client import RpcClient, zero_client, User

# Create client wrapper
client = RpcClient(zero_client)

# Use with full type safety
user = User(id=1, name="Alice", email="alice@example.com")
result = client.save_user(user)
print(result)

# Get user with type hints
retrieved_user = client.get_user(1)
print(f"User: {retrieved_user.name}")
```

## Generation Options

### Specify Protocol

```bash
# ZeroMQ (default)
python -m zero.generate_client --host localhost --port 5559 --protocol zmq

# TCP
python -m zero.generate_client --host localhost --port 5559 --protocol tcp
```

### Generate Async Client

```bash
python -m zero.generate_client \
  --host localhost \
  --port 5559 \
  --protocol zmq \
  --async \
  --overwrite-dir ./async_client
```

### Specify Output Directory

```bash
python -m zero.generate_client \
  --host localhost \
  --port 5559 \
  --overwrite-dir ./my_custom_client_path
```

## Generated Code Example

### Synchronous Client

```python
from dataclasses import dataclass
from msgspec import Struct
from datetime import datetime

from zero import ZeroClient

zero_client = ZeroClient("localhost", 5559)

class Person(Struct):
    name: str
    age: int
    dob: datetime

@dataclass
class Order:
    id: int
    amount: float
    created_at: datetime

class RpcClient:
    def __init__(self, zero_client: ZeroClient):
        self._zero_client = zero_client

    def save_person(self, person: Person) -> bool:
        return self._zero_client.call("save_person", person)

    def save_order(self, order: Order) -> bool:
        return self._zero_client.call("save_order", order)
```

### Async Client

```bash
python -m zero.generate_client \
  --host localhost \
  --port 5559 \
  --async \
  --overwrite-dir ./async_client
```

```python
import asyncio
from async_client import RpcClient, zero_client, Person, Order

async def main():
    client = RpcClient(zero_client)

    # Call async methods
    person = Person(name="Alice", age=30, dob=datetime(1993, 1, 1))
    result = await client.save_person(person)
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
```

## Remote Server Generation

Generate clients for servers on different machines:

```bash
python -m zero.generate_client \
  --host 192.168.1.100 \
  --port 5559 \
  --protocol tcp \
  --overwrite-dir ./remote_client
```

## Best Practices

✅ **DO:**

- Regenerate clients when server schema changes
- Keep generated code in version control
- Use type hints from generated code

❌ **DON'T:**

- Edit generated code manually (it will be overwritten)
- Keep old generated code when schemas change
- Forget to regenerate when adding new RPC methods

## Troubleshooting

### "Connection refused"

Make sure the server is running:

```bash
python server.py
```

### "Protocol not found"

Ensure the protocol matches the server:

- Server uses ZeroMQ → use `--protocol zmq`
- Server uses TCP → use `--protocol tcp`

### Generated code not updating

Use the `--overwrite-dir` flag to force regeneration:

```bash
python -m zero.generate_client \
  --host localhost \
  --port 5559 \
  --overwrite-dir ./generated_client
```

## Next Steps

- [Async/Await](async-await.md) - Learn about async clients
- [Serialization](serialization.md) - Understand data types
- [TCP Protocol](tcp-protocol.md) - Improve performance
