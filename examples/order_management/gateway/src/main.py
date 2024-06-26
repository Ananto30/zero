import logging

from aiohttp import web

from zero import AsyncZeroClient

log = logging.getLogger(__name__)

auth_service = AsyncZeroClient("auth", 6000)
user_service = AsyncZeroClient("user", 6001)
order_service = AsyncZeroClient("order", 6002)


async def login(request):
    data = await request.json()
    username = data.get("username")
    password = data.get("password")
    jwt = await user_service.call("login", (username, password))
    if "error" in jwt:
        return web.json_response(jwt, status=401)
    return web.json_response({"jwt": jwt})


async def profile(request):
    jwt = request.headers.get("Authorization")
    if not jwt:
        return web.json_response({"error": "Missing Authorization header"}, status=401)
    jwt = jwt.split(" ")[1]
    auth = await auth_service.call("verify_jwt", jwt)
    if "error" in auth:
        return web.json_response(auth, status=401)

    username = auth.get("username")
    user = await user_service.call("get_user", username)
    return web.json_response(user)


async def get_orders(request):
    jwt = request.headers.get("Authorization")
    if not jwt:
        return web.json_response({"error": "Missing Authorization header"}, status=401)
    jwt = jwt.split(" ")[1]
    auth = await auth_service.call("verify_jwt", jwt)
    if "error" in auth:
        return web.json_response(auth, status=401)

    username = auth.get("username")
    user = await user_service.call("get_user", username)
    orders = await order_service.call("get_orders", user.get("id"))
    return web.json_response(orders)


async def add_order(request):
    jwt = request.headers.get("Authorization")
    if not jwt:
        return web.json_response({"error": "Missing Authorization header"}, status=401)
    jwt = jwt.split(" ")[1]
    auth = await auth_service.call("verify_jwt", jwt)
    if "error" in auth:
        return web.json_response(auth, status=401)

    request_data = await request.json()
    items = request_data.get("items")

    username = auth.get("username")
    user = await user_service.call("get_user", username)
    data = {"user_id": user.get("id"), "items": items}
    created = await order_service.call("add_order", data)
    if created:
        return web.json_response({"status": "success"})
    return web.json_response({"error": "Failed to create order"}, status=500)


app = web.Application()
app.router.add_post("/api/v1/login", login)
app.router.add_get("/api/v1/profile", profile)
app.router.add_get("/api/v1/orders", get_orders)
app.router.add_post("/api/v1/orders", add_order)
