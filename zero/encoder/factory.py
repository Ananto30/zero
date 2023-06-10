from .msgspc import MsgspecEncoder
from .protocols import Encoder


def get_encoder(name: str) -> Encoder:
    if name == "msgspec":
        return MsgspecEncoder()

    raise ValueError(f"unknown encoder: {name}")
