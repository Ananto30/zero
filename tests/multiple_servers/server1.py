from zero import ZeroServer


def echo(msg: str) -> str:
    return "Server1: " + msg


def hello() -> str:
    return "Hello from server1"


def run(port):
    print("Starting server1 on port", port)
    app = ZeroServer(port=port)
    app.register_rpc(echo)
    app.register_rpc(hello)
    app.run(2)
