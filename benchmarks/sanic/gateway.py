import httpx
from sanic import Sanic
from sanic.response import text, json

app = Sanic("My Hello, world app")


@app.route('/')
async def test(request):
    async with httpx.AsyncClient() as client:
        r = await client.post("http://localhost:8011/order", json={"user_id": "1", "items": ['apple', 'python']})
        return json(r.json())


@app.route('/hello')
async def test(request):
    async with httpx.AsyncClient() as client:
        r = await client.get("http://localhost:8011/hello")
        return text(r.text)

if __name__ == '__main__':
    app.run()
