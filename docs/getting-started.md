# Getting Started

Welcome to Zero! This guide will help you get up and running with your first RPC server and client.

## Prerequisites

- Python 3.9 or higher
- pip package manager

## Installation

### Basic Installation

```bash
pip install zeroapi
```

### With Optional Features

Depending on your needs, you can install additional features:

```bash
# For better async performance on Linux/macOS
pip install "zeroapi[uvloop]"

# For Pydantic model support
pip install "zeroapi[pydantic]"

# For Windows async support
pip install "zeroapi[tornado]"

# Install all optional dependencies
pip install "zeroapi[all]"
```

## Your First RPC Server

Create a file called `server.py`:

```python
from zero import ZeroServer

app = ZeroServer(port=5559)

@app.register_rpc
def echo(msg: str) -> str:
    """Echo back the message you send"""
    return msg

@app.register_rpc
async def hello_world() -> str:
    """Return a hello world message"""
    return "hello world"

if __name__ == "__main__":
    app.run()
```

**Important Notes:**

- Always run `ZeroServer` under `if __name__ == "__main__":` (uses multiprocessing)
- Type hints are **required** for all RPC function arguments and returns
- Support one argument at a time (for now)

## Your First RPC Client

Create a file called `client.py`:

```python
from zero import ZeroClient

zero_client = ZeroClient("localhost", 5559)

# Call synchronous methods
echo_response = zero_client.call("echo", "Hi there!")
print(echo_response)  # Output: Hi there!

hello_response = zero_client.call("hello_world", None)
print(hello_response)  # Output: hello world
```

## Run the Example

**Terminal 1** - Start the server:

```bash
python server.py
```

**Terminal 2** - Run the client:

```bash
python client.py
```

You should see:

```
Hi there!
hello world
```

## Next Steps

- Learn about [async/await](guides/async-await.md)
- Explore [serialization options](guides/serialization.md)
- Try [TCP protocol](guides/tcp-protocol.md) for better performance
- Use [code generation](guides/code-generation.md) for generating client code

## Need Help?

- Check out [Examples](examples/basic-echo.md)
- Read the [API Reference](api/server.md)
- Open an issue on [GitHub](https://github.com/Ananto30/zero)
