import asyncio

from store import Base, create_order, engine


async def create_demo_data():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

        await create_order(1, ["apple", "orange"])
        await create_order(1, ["python", "boa"])
        await create_order(2, ["pizza", "burger", "coca-cola"])


if __name__ == "__main__":
    asyncio.run(create_demo_data())
