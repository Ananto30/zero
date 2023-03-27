from .msgpk import MsgPackEncoder
from .protocols import Encoder


def get_encoder(name: str) -> Encoder:
    if name == "msgpack":
        return MsgPackEncoder()  # type: ignore

    raise ValueError("Unknown encoder: %s" % name)
