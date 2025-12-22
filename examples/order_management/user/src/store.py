from typing import Optional

from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.future import select
from sqlalchemy.orm import DeclarativeBase

DATABASE_URL = "sqlite+aiosqlite:///./test.db"

engine = create_async_engine(DATABASE_URL, future=True, echo=False)
async_session = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)  # No hashing, it's a demo


async def create_user(username: str, password: str):
    async with async_session() as session:
        user = User(username=username, password=password)
        session.add(user)
        await session.commit()


async def get_user_by_username(username: str) -> Optional[User]:
    async with async_session() as session:
        return (
            await session.execute(select(User).filter(User.username == username))
        ).scalar_one_or_none()


async def get_user_by_username_and_password(username: str, password: str) -> Optional[User]:
    async with async_session() as session:
        return (
            await session.execute(
                select(User).filter(User.username == username, User.password == password)
            )
        ).scalar_one_or_none()
