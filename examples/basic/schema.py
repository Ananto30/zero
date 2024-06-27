from dataclasses import dataclass
from datetime import date
from typing import List

import msgspec


class Address(msgspec.Struct):
    street: str
    city: str
    zip: int


class User(msgspec.Struct):
    name: str
    age: int
    emails: List[str]
    addresses: List[Address]
    registered_at: date


@dataclass
class Teacher:
    name: str


class Student(User):
    roll_no: int
    marks: List[int]
    teachers: List[Teacher]
