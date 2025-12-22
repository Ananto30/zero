# ZeroClient API Reference

## Overview

`ZeroClient` is the synchronous client for calling RPC methods on a Zero server.

## Constructor

```python
ZeroClient(
    host: str,
    port: int,
    default_timeout: int = 5000,
    encoder: Type[Encoder] = GenericEncoder,
    protocol: Type[ZeroClientProtocol] = ZMQClient,
    pool_size: int = 50,
)
```

### Parameters

- **host** (str): Server hostname or IP address.
- **port** (int): Server port number.
- **default_timeout** (int): Default timeout for calls in milliseconds. Default: 5000
- **encoder** (Encoder): Message encoder matching server. Default: Msgspec
- **protocol** (ClientProtocol): Communication protocol. Default: ZeroMQ
    - `zero.protocols.zeromq.ZeroMQClient` - ZeroMQ (default)
    - `zero.protocols.tcp.TCPClient` - Raw TCP
- **pool_size** (int): Connection pool size for reusing connections. Default: 50

### Example

```python
from zero import ZeroClient

client = ZeroClient(
    host="192.168.1.100",
    port=5559,
)
```

## Methods

### call

Call an RPC method on the server.

```python
def call(
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

**Returns:** Response from the server

**Raises:** Exception if server returns error

### Example

```python
from zero import ZeroClient
from dataclasses import dataclass

@dataclass
class User:
    id: int
    name: str
    email: str

client = ZeroClient("localhost", 5559)

# Simple call
name = client.call("greet", "Alice")
print(name)  # Output: Hello, Alice!

# Call with return type conversion
user = client.call("get_user", 1, return_type=User)
print(user.name)

# Call with complex argument
result = client.call("transfer_money", {
    "from": "Alice",
    "to": "Bob",
    "amount": 100
})
```

### Type Conversion

```python
from dataclasses import dataclass

@dataclass
class Product:
    id: int
    name: str
    price: float

# Automatic conversion to dataclass
product = client.call(
    "get_product",
    123,
    return_type=Product
)
```

## Connection Management

Connections are persistent and reused:

```python
client = ZeroClient("localhost", 5559)

# First call establishes connection
result1 = client.call("method1", "data1")

# Second call reuses connection
result2 = client.call("method2", "data2")

# Connection is automatically managed
```

## Protocol Selection

### ZeroMQ (Default)

Best for complex messaging patterns:

```python
client = ZeroClient("localhost", 5559)
# Automatically uses ZeroMQ
```

### TCP

Best for performance:

```python
from zero.protocols.tcp import TCPClient

client = ZeroClient("localhost", 5559, protocol=TCPClient)
```

## Custom Encoder

```python
from my_encoder import MyCustomEncoder

client = ZeroClient(
    "localhost", 5559,
    encoder=MyCustomEncoder
)
```

## Complete Example

```python
from zero import ZeroClient
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Order:
    id: int
    total: float
    created_at: datetime

client = ZeroClient("localhost", 5559)

# Create order
created = client.call("create_order", {
    "items": 3,
    "total": 99.99
})

# Get order details
order = client.call("get_order", created, return_type=Order)
print(f"Order {order.id}: ${order.total}")

# Update order
updated = client.call("update_order", {
    "id": created,
    "status": "shipped"
})
```

## Best Practices

✅ **DO:**

- Reuse client instance for multiple calls
- Use type hints with `return_type` parameter
- Handle connection errors gracefully
- Use TCP for high-performance scenarios

❌ **DON'T:**

- Create new client for each call
- Use synchronous client in async code (use AsyncZeroClient instead)

## Next Steps

- [AsyncZeroClient](async-client.md) - Async client for concurrent calls
- [ZeroServer](server.md) - Server configuration
- [Guides - Code Generation](../guides/code-generation.md) - Auto-generate typed clients
