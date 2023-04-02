import msgpack


class MsgPackEncoder:
    def __init__(self):
        pass

    def encode(self, data):
        return msgpack.packb(data)

    def decode(self, data):
        return msgpack.unpackb(data)
