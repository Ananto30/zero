import msgspec

# Have to put here to make it fork-safe
encoder = msgspec.msgpack.Encoder()
decoder = msgspec.msgpack.Decoder()


class MsgspecEncoder:
    def __init__(self):
        pass

    def encode(self, data):
        return encoder.encode(data)

    def decode(self, data):
        return decoder.decode(data)

    def decode_type(self, data, typ):
        return msgspec.msgpack.decode(data, type=typ)
