from zero import ZeroServer


def echo(msg: str) -> str:
    return "Server1: " + msg


def hello() -> str:
    return "Hello from server1"


def run():
    app = ZeroServer(port=7777)
    app.register_rpc(echo)
    app.register_rpc(hello)
    app.run()
