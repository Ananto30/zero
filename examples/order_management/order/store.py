from enum import IntEnum
from typing import List, Optional

from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.future import select
from sqlalchemy.orm import Session, declarative_base, sessionmaker
from datetime import datetime

DATABASE_URL = "sqlite+aiosqlite:///./test.db"

engine = create_async_engine(DATABASE_URL, future=True, echo=True)
async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
Base = declarative_base()


def now():
    return datetime.now().isoformat()


class OrderStatus(IntEnum):
    CREATED = 1
    PAID = 2
    CANCELLED = 3


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    placed_at = Column(String, nullable=False, default=now)
    items = Column(String, nullable=False)
    status = Column(Integer, nullable=False)

    def set_items(self, items):
        self.items = ",".join(items)

    def get_items(self):
        return self.items.split(",")


async def create_order(user_id: int, items: List[str]):
    async with async_session() as session:
        order = Order(user_id=user_id, status=OrderStatus.CREATED)
        order.set_items(items)
        session.add(order)
        await session.commit()


async def get_order_by_id(order_id: int) -> Optional[Order]:
    async with async_session() as session:
        row = await session.execute(select(Order).filter(Order.id == order_id))
        res = row.scalars().first()
        return row2dict(res) if res else None


async def get_orders_by_user_id(user_id: int) -> List[Order]:
    async with async_session() as session:
        rows = await session.execute(select(Order).filter(Order.user_id == user_id))
        res = rows.scalars()
        return [row2dict(row) for row in res]


def row2dict(row):
    d = {}
    for column in row.__table__.columns:
        d[column.name] = str(getattr(row, column.name))

    return d
