# TCP Protocol

By default, Zero uses ZeroMQ for communication. However, you can use raw TCP for even better performance!

## Why TCP?

- 🚀 **Better performance** - 100k+ req/s with TCP vs 40k req/s with ZeroMQ
- 📊 **Lower latency** - 2.33ms at 99th percentile vs 4.41ms
- ⚡ **Simpler protocol** - Direct TCP connection

## ⚠️ Important Note

- TCP protocol is only supported in unix-based systems (Linux, macOS). Windows is not supported.
- Only supports async clients. (Server functions can be sync or async)
- Server and client both need to use TCP protocol to communicate.

## Enabling TCP

### Server

```python
from zero import ZeroServer
from zero.protocols.tcp import TCPServer

app = ZeroServer(port=5559, protocol=TCPServer)

@app.register_rpc
def echo(msg: str) -> str:
    return msg

@app.register_rpc
async def hello_world() -> str:
    return "hello world"

if __name__ == "__main__":
    app.run()
```

### Client

```python
from zero import AsyncZeroClient
from zero.protocols.tcp import AsyncTCPClient

client = AsyncZeroClient("localhost", 5559, protocol=AsyncTCPClient)

# Use normally
response = client.call("echo", "Hi!")
print(response)
```

## Performance Comparison

| Protocol  | hello world (req/s) | 99% latency (ms) | redis save (req/s) | 99% latency (ms) |
| --------- | ------------------- | ---------------- | ------------------ | ---------------- |
| **TCP**   | **100,752**         | **2.33**         | **35,813**         | **13.48**        |
| ZMQ Async | 41,092              | 4.41             | 23,996             | 8.64             |
| ZMQ Sync  | 27,571              | 6.65             | 10,269             | 23.71            |

_Results from 13th Gen Intel i9-13900HK, Docker in Ubuntu 22.04_

## Connection Management

TCP connections are persistent and reused. So create the client once and reuse it:

```python
from zero import ZeroClient
from zero.protocols.tcp import TCPClient

client = ZeroClient("localhost", 5559, protocol=TCPClient)

# First call - establishes connection
result1 = client.call("echo", "first")

# Second call - reuses connection
result2 = client.call("echo", "second")

# Connection is reused automatically
```

## Best Practices

✅ **DO:**

- Keep connections alive for repeated calls
- Use connection pooling for multiple clients (`pool_size` parameter)
- Build async services with TCP for best performance

❌ **DON'T:**

- Create new client for each call (reuse the connection)
- Use TCP client in sync code
- Server use TCP with a ZeroMQ client or vice versa

## Next Steps

- [Code Generation](code-generation.md) - Auto-generate typed clients
- [Async/Await](async-await.md) - Build async services with TCP
- [Benchmarks](../benchmarks.md) - See performance comparisons
