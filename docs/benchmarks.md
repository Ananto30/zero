# Benchmarks

Zero is built for performance. Here's how it compares to other frameworks.

## Test Environment

- **Hardware**: 13th Gen Intel Core i9-13900HK @ 5.40GHz
- **Cores**: 14 cores, 20 threads
- **RAM**: 32GB
- **OS**: Ubuntu 24.04 LTS
- **Containerization**: Docker

## Test Scenarios

### Scenario 1: Simple Hello World

A simple endpoint returning a constant response. Tests baseline throughput and latency.

**Endpoint**: `/hello` - Returns "hello world"

### Scenario 2: Redis Save

Tests I/O performance - each request saves an Order object to Redis.

**Endpoint**: `/order` - Saves order data to Redis

## Results

| Framework      | hello world (req/s) | 99% latency (ms) | redis save (req/s) | 99% latency (ms) |
| -------------- | ------------------- | ---------------- | ------------------ | ---------------- |
| **zero (tcp)** | **100,752**         | **2.33**         | **35,813**         | **13.48**        |
| sanic          | 58,811              | 4.43             | 23,623             | 9.22             |
| zero (async)   | 41,092              | 4.41             | 23,996             | 8.64             |
| blacksheep     | 38,026              | 8.41             | 16,324             | 13.54            |
| aiohttp        | 33,168              | 11.89            | 17,959             | 12.76            |
| zero (sync)    | 27,571              | 6.65             | 10,269             | 23.71            |
| aiozmq         | 25,174              | 6.13             | 8,850              | 10.19            |
| fastapi        | 19,683              | 9.09             | 12,776             | 16.28            |

### When Zero is Best

- Building RPC microservices
- High throughput is needed (10k+ req/s)
- Low latency is critical
- Simple request-response patterns
- Optimizing infrastructure costs

### When Other Frameworks Might Be Better

- Complex routing requirements
- REST API conventions
- HTML templating

## Running Benchmarks

Zero includes benchmark tools for testing against other frameworks.

See [benchmarks/dockerize](https://github.com/Ananto30/zero/tree/main/benchmarks/dockerize) for setup instructions.

## Performance Tips

To maximize Zero performance:

1. **Use TCP protocol** instead of ZeroMQ

    ```python
    from zero.protocols.tcp import TCPServer
    app = ZeroServer(protocol=TCPServer)
    ```

2. **Use async for I/O** operations

    ```python
    @app.register_rpc
    async def fetch_data(url: str) -> str:
        # Async I/O here
    ```

3. **Reuse client connections**

    ```python
    client = ZeroClient("localhost", 5559)
    # Reuse for multiple calls
    ```

4. **Avoid blocking operations** in RPC handlers

5. **Use appropriate worker count**

    ```python
    app = ZeroServer(workers=None)  # Default: CPU cores
    ```

6. **Keep messages small** - Reduces serialization overhead

## Further Reading

- [TCP Protocol Guide](guides/tcp-protocol.md)
- [Async/Await Guide](guides/async-await.md)
- [Performance Tips](guides/basic-usage.md#best-practices)
- [GitHub Benchmark Code](https://github.com/Ananto30/zero/tree/main/benchmarks)
