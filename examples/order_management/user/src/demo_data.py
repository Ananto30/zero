import asyncio

from src.store import Base, create_user, engine


async def create_demo_data():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

        await create_user("user1", "password1")
        await create_user("user2", "password2")


if __name__ == "__main__":
    asyncio.run(create_demo_data())
