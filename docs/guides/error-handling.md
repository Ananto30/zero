# Error Handling

Server exceptions are propagated to the client:

## Server-Side

```python
from zero import ZeroServer

app = ZeroServer(port=5559)

@app.register_rpc
def divide(numbers: dict) -> float:
    return numbers['a'] / numbers['b']

if __name__ == "__main__":
    app.run()
```

## Client-Side

```python
from zero import ZeroClient

client = ZeroClient("localhost", 5559)

result = client.call("divide", {"a": 10, "b": 0})
print(result)
```

This will raise a `zero.error.RemoteException` on the client side indicating a division by zero error.

Output:

```bash
Traceback (most recent call last):
  File "client.py", line 5, in <module>
    result = client.call("divide", {"a": 10, "b": 0})
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "venv/lib/python3.11/site-packages/zero/rpc/client.py", line 130, in call
    check_response(resp_data)
  File "venv/lib/python3.11/site-packages/zero/rpc/client.py", line 272, in check_response
    raise RemoteException(exc)
zero.error.RemoteException: ZeroDivisionError('division by zero')
```

For traceback details, check the server logs.
