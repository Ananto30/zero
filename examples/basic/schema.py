from typing import List

import msgspec


class User(msgspec.Struct):
    name: str
    age: int
    emails: List[str]
