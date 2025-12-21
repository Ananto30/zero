# Serialization

Zero supports multiple serialization formats for passing complex data types between client and server.

## Default: Msgspec

[Msgspec](https://jcristharif.com/msgspec/) is the default serializer - it's fast, efficient, and supports [many data types](https://jcristharif.com/msgspec/supported-types.html).

### Using Dataclasses

```python
from dataclasses import dataclass
from datetime import datetime
from zero import ZeroServer

app = ZeroServer(port=5559)

@dataclass
class Product:
    id: int
    name: str
    price: float
    created_at: datetime

@app.register_rpc
def create_product(product: Product) -> bool:
    print(f"Created: {product.name} at ${product.price}")
    return True

if __name__ == "__main__":
    app.run()
```

### Using msgspec.Struct

```python
from msgspec import Struct
from datetime import datetime
from zero import ZeroServer

app = ZeroServer(port=5559)

class Order(Struct):
    id: int
    amount: float
    customer: str
    created_at: datetime

@app.register_rpc
def save_order(order: Order) -> bool:
    print(f"Order {order.id}: ${order.amount}")
    return True

if __name__ == "__main__":
    app.run()
```

## Pydantic Support

Use Pydantic models with the `pydantic` extra:

```bash
pip install "zeroapi[pydantic]"
```

```python
from pydantic import BaseModel, Field
from datetime import datetime
from zero import ZeroServer

app = ZeroServer(port=5559)

class User(BaseModel):
    id: int = Field(..., gt=0)
    name: str = Field(..., min_length=1)
    email: str
    age: int = Field(..., ge=18)
    created_at: datetime = Field(default_factory=datetime.now)

@app.register_rpc
def create_user(user: User) -> bool:
    print(f"Created user: {user.name}")
    return True

if __name__ == "__main__":
    app.run()
```

## Supported Types

Zero supports these types out of the box: [supported types](https://jcristharif.com/msgspec/supported-types.html)

## Custom Serializer

For custom serialization needs, implement the `Encoder` interface:

```python
from zero.encoder.protocols import Encoder
from typing import Any, Type

class MyCustomEncoder(Encoder):
    def encode(self, obj: Any) -> bytes:
        """Serialize Python object to bytes"""
        # Your serialization logic here
        return b"..."

    def decode(self, data: bytes, type_hint: Type[Any]) -> Any:
        """Deserialize bytes to Python object"""
        # Your deserialization logic here
        return {}
```

### Using Custom Encoder

```python
from zero import ZeroServer, ZeroClient
from my_encoder import MyCustomEncoder

# Server
app = ZeroServer(port=5559, encoder=MyCustomEncoder)

# Client
client = ZeroClient("localhost", 5559, encoder=MyCustomEncoder)
```

**Important:** Use the same encoder on both server and client!

## Return Type Conversion

Specify the return type to automatically convert responses:

```python
from zero import ZeroClient
from dataclasses import dataclass

@dataclass
class Product:
    id: int
    name: str
    price: float

client = ZeroClient("localhost", 5559)

# The response will be automatically converted to Product
product = client.call("get_product", 1, return_type=Product)

print(product.name)
```

## Performance Tips

1. **Use msgspec.Struct** over dataclasses for better performance
2. **Avoid deeply nested structures** - flatten when possible
3. **Use appropriate types** - let the serializer optimize for you
4. **Consider message size** - larger messages take longer to serialize/deserialize

## Next Steps

- [Async/Await](async-await.md) - Build async services
- [Code Generation](code-generation.md) - Auto-generate typed clients
- [TCP Protocol](tcp-protocol.md) - Improve performance
