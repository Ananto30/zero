import msgpack


class Btypes:
    def pack(self):
        values = vars(self)
        for k, v in values.items():
            if isinstance(v, Btypes):
                values[k] = v.pack()
        return msgpack.packb(values)

    @classmethod
    def unpack(cls, d):
        return cls(**msgpack.unpackb(d, raw=False))

    def get_all_vars(self):
        values = vars(self)
        for k, v in values.items():
            if isinstance(v, Btypes):
                values[k] = vars(v)
        return values


class Etypes(Btypes):
    def __init__(self, operation: str, request, response=None):
        self.operation = operation
        self.request = request
        self.response = response


class TypeCheckFailedException(Exception):
    pass


def type_check(o, t):
    if not isinstance(o, t):
        raise TypeCheckFailedException
