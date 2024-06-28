import logging
import typing

import jwt

from zero import ZeroServer

from .schema import Student, Teacher, User

app = ZeroServer(port=5559)


async def echo(msg: str) -> str:
    return msg


async def hello_world() -> str:
    return "hello world"


async def decode_jwt(msg: str) -> dict:
    decoded_jwt = jwt.decode(msg, "secret", algorithms=["HS256"])
    logging.info(decoded_jwt)
    return decoded_jwt


async def sum_list(msg: typing.List[int]) -> int:
    return sum(msg)


async def two_rets(msg: str) -> typing.Tuple[int, int]:
    return 1, 2


@app.register_rpc
def hello_user(user: User) -> str:
    return f"Hello {user.name}! You are {user.age} years old. Your email is {user.emails[0]}!"


@app.register_rpc
def hello_users(users: typing.List[User]) -> str:
    return f"Hello {', '.join([user.name for user in users])}! Your emails are {', '.join([email for user in users for email in user.emails])}!"


teachers = [
    Teacher(name="Teacher1"),
    Teacher(name="Teacher2"),
]


@app.register_rpc
def hello_student(student: Student) -> str:
    return f"Hello {student.name}! You are {student.age} years old. Your email is {student.emails[0]}! Your roll no. is {student.roll_no} and your marks are {student.marks}!"


if __name__ == "__main__":
    app.register_rpc(echo)
    app.register_rpc(hello_world)
    app.register_rpc(decode_jwt)
    app.register_rpc(sum_list)
    app.register_rpc(two_rets)
    app.run()
