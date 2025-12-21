# Zero - Fast Python RPC Framework

<p align="center">
    <img height="300px" src="https://ananto30.github.io/i/1200xCL_TP.png" />
</p>

**Zero** is a simple Python RPC framework to build **fast and high performance microservices** or distributed servers.

## Key Features

- ⚡ **Faster communication** between microservices using [ZeroMQ](https://zeromq.org/) or raw TCP
- 💬 **Message-based** communication with traditional client-server patterns
- 🔄 Support for both **async** and **sync**
- 🚀 **Multi-core support** - Base server utilizes all CPU cores
- 📦 Built-in schema support (**Msgspec**, **Pydantic**)
- 🤖 **Client Code generation** with schema support
- 📊 Exceptional performance - See [benchmarks](benchmarks.md)

## Philosophy

- **Zero Learning Curve**: Add functions and spin up a server - literally that's it! The framework hides the complexity of messaging patterns.
- **ZeroMQ Power**: Built on the awesome ZeroMQ library for reliable, fast inter-service communication.

## Quick Start

```python
from zero import ZeroServer

app = ZeroServer(port=5559)

@app.register_rpc
def echo(msg: str) -> str:
    return msg

if __name__ == "__main__":
    app.run()
```

Call the server:

```python
from zero import ZeroClient

client = ZeroClient("localhost", 5559)
print(client.call("echo", "Hello World!"))
```

## Installation

```bash
pip install zeroapi
```

For additional features:

```bash
pip install "zeroapi[uvloop]"      # Better async performance
pip install "zeroapi[pydantic]"    # Pydantic support
pip install "zeroapi[tornado]"     # Windows async support
pip install "zeroapi[all]"         # All extras
```

## Documentation

Explore the full documentation to get started:

- [Getting Started](getting-started.md) - Installation and basic setup
- [Guides](guides/installation.md) - Detailed guides for all features
- [Examples](examples/basic-echo.md) - Real-world examples
- [API Reference](api/server.md) - Complete API documentation
- [Benchmarks](benchmarks.md) - Performance comparisons

## Performance

Zero achieves exceptional performance across different protocols:

| Protocol | hello world (req/s) | 99% latency (ms) |
| -------- | ------------------- | ---------------- |
| **TCP**  | **100,752**         | **2.33**         |
| Async    | 41,092              | 4.41             |
| Sync     | 27,571              | 6.65             |

See full [benchmarks](benchmarks.md) for more frameworks.

## Contributing

Contributions are welcome! Please check out our [contributing guide](contributing.md).

## License

MIT License - see LICENSE file for details

---

**Please leave a ⭐ if you like Zero!**

[!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/ananto30)
