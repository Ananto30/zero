import httpx
from fastapi import FastAPI

app = FastAPI()


@app.get("/")
async def root():
    async with httpx.AsyncClient() as client:
        r = await client.post("http://localhost:8011/order", json={"user_id": "1", "items": ['apple', 'python']})
        return r.json()
