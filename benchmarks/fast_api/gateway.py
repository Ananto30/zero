import httpx
from fastapi import FastAPI

app = FastAPI()


@app.get("/order")
async def root():
    async with httpx.AsyncClient() as client:
        r = await client.post("http://localhost:8011/order", json={"user_id": "1", "items": ['apple', 'python']})
        return r.json()


@app.get("/hello")
async def root():
    async with httpx.AsyncClient() as client:
        r = await client.get("http://localhost:8011/hello")
        return r.json()
