# ZeroServer API Reference

## Overview

`ZeroServer` is the main server class for creating RPC endpoints with Zero.

## Constructor

```python
ZeroServer(
    host: str = "0.0.0.0",
    port: int = 5559,
    encoder: Type[Encoder] = GenericEncoder,
    protocol: Type[ZeroServerProtocol] = ZMQServer,
    use_threads: bool = False,
)
```

### Parameters

- **host** (str): Host address to bind to. Default: "0.0.0.0" (all interfaces)
- **port** (int): Port number to listen on. Default: 5559
- **encoder** (Encoder): Custom message encoder. Default: Msgspec
- **protocol** (ServerProtocol): Communication protocol. Default: ZeroMQ
    - `zero.protocols.zeromq.ZeroMQServer` - ZeroMQ (default)
    - `zero.protocols.tcp.TCPServer` - Raw TCP
- **use_threads** (bool): Use threads instead of processes. Default: False

### Example

```python
from zero import ZeroServer
from zero.protocols.tcp import TCPServer

app = ZeroServer(
    port=5559,
    host="127.0.0.1",
    protocol=TCPServer
)
```

## Methods

### register_rpc

Decorator to register RPC methods.

```python
@app.register_rpc
def my_function(arg: str) -> str:
    return arg.upper()
```

**Requirements:**

- Type hints required for arguments and return value
- Single argument (or use dataclass/dict for multiple values)
- Return type must be supported

### run

Start the RPC server and listen for requests.

```python
if __name__ == "__main__":
    app.run()
```

Starts the server with configured number of workers.

## Complete Example

```python
from zero import ZeroServer
from dataclasses import dataclass

app = ZeroServer(port=5559)

@dataclass
class Product:
    id: int
    name: str
    price: float

@app.register_rpc
def get_product(product_id: int) -> Product:
    """Get a product by ID"""
    return Product(id=product_id, name="Laptop", price=999.99)

@app.register_rpc
def update_product(product: Product) -> bool:
    """Update product details"""
    print(f"Updated {product.name}")
    return True

@app.register_rpc
async def calculate_price(data: dict) -> float:
    """Calculate final price with tax"""
    import asyncio
    await asyncio.sleep(0.1)
    return data['price'] * 1.1

if __name__ == "__main__":
    app.run()
```

## Configuration Tips

### Performance Tuning

```python
# Use all available CPU cores
app = ZeroServer(port=5559)
app.run()

# Use fewer workers for testing
app = ZeroServer(port=5559)
app.run(workers=2)

# Use TCP protocol for better performance
from zero.protocols.tcp import TCPServer
app = ZeroServer(port=5559, protocol=TCPServer)
```

### Custom Serialization

```python
from my_encoder import MyCustomEncoder
app = ZeroServer(port=5559, encoder=MyCustomEncoder)
```

## Multiprocessing Notes

- Server must be started under `if __name__ == "__main__":`
- Global state is instantiated in each worker process
- Database connections should be created per-worker
- Avoid global mutable state

## Next Steps

- [ZeroClient](client.md) - Create clients
- [AsyncZeroClient](async-client.md) - Async clients
