from zero.rpc.server import ZeroServer

PORT = 7777
HOST = "localhost"


app = ZeroServer(port=PORT, use_threads=True)


@app.register_rpc
async def hello_world() -> str:
    return "hello world"


if __name__ == "__main__":
    app.run(2)
