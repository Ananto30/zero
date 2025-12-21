# Basic Usage

## Creating a Server

### Simple RPC Server

```python
from zero import ZeroServer

app = ZeroServer(port=5559)

@app.register_rpc
def add(numbers: dict) -> int:
    """Add two numbers"""
    return numbers['a'] + numbers['b']

@app.register_rpc
def greet(name: str) -> str:
    """Greet someone"""
    return f"Hello, {name}!"

if __name__ == "__main__":
    app.run()
```

### Server Configuration

```python
from zero import ZeroServer

app = ZeroServer(
    port=5559,             # Port to listen on
    host="0.0.0.0",        # Host address (0.0.0.0 = all interfaces)
    workers=4,             # Number of worker processes (default: CPU count)
)
```

## Creating a Client

### Synchronous Client

```python
from zero import ZeroClient

client = ZeroClient("localhost", 5559)

# Call a function
result = client.call("add", {"a": 5, "b": 3})
print(result)  # Output: 8

greeting = client.call("greet", "Alice")
print(greeting)  # Output: Hello, Alice!
```

### Connecting to Remote Server

```python
from zero import ZeroClient

# Connect to a server on another machine
client = ZeroClient("192.168.1.100", 5559)
result = client.call("add", {"a": 10, "b": 20})
```

## Type Hints

Type hints are **required** for all RPC functions. [supported types](https://jcristharif.com/msgspec/supported-types.html)

## Best Practices

✅ **DO:**

- Use type hints for all arguments and returns
- Put `run` instruction under `if __name__ == "__main__":`
- Use meaningful function names
- Document your RPC functions

❌ **DON'T:**

- Use global state (instantiate in `if __name__ == "__main__":`)
- Use functions with multiple arguments (use dict/dataclass/tuple instead)
- Make blocking RPC calls in async functions

## Next Steps

- [Serialization](serialization.md) - Handle complex data types
- [Async/Await](async-await.md) - Build async services
- [Code Generation](code-generation.md) - Auto-generate clients
