import logging

from aiohttp import web

from zero.error import RemoteException

from .generated_client.auth_client import RpcClient as AuthClient
from .generated_client.auth_client import zero_client as auth_client
from .generated_client.order_client import OrderReq
from .generated_client.order_client import RpcClient as OrderClient
from .generated_client.order_client import zero_client as order_client
from .generated_client.user_client import RpcClient as UserClient
from .generated_client.user_client import zero_client as user_client

log = logging.getLogger(__name__)

auth_service = AuthClient(auth_client)
user_service = UserClient(user_client)
order_service = OrderClient(order_client)


async def extract_and_verify_jwt(request):
    """Extract JWT from Authorization header and verify it."""
    jwt = request.headers.get("Authorization")
    if not jwt:
        return None, web.json_response(
            {"error": "Missing Authorization header"}, status=401
        )

    jwt = jwt.split(" ")[1]
    try:
        auth = await auth_service.verify_jwt(jwt)
    except RemoteException as e:
        log.exception("JWT verification failed", e)
        return None, web.json_response({"error": str(e)}, status=401)

    return auth, None


async def login(request):
    data = await request.json()
    username = data.get("username")
    password = data.get("password")

    try:
        jwt = await user_service.login((username, password))
    except RemoteException as e:
        return web.json_response({"error": str(e)}, status=401)

    return web.json_response({"jwt": jwt})


async def profile(request):
    auth, error = await extract_and_verify_jwt(request)
    if error:
        return error

    user = await user_service.get_user(auth.username)
    return web.json_response(user)


async def get_orders(request):
    auth, error = await extract_and_verify_jwt(request)
    if error:
        return error

    user = await user_service.get_user(auth.username)
    orders = await order_service.get_orders(user.id)
    return web.json_response(orders)


async def add_order(request):
    auth, error = await extract_and_verify_jwt(request)
    if error:
        return error

    request_data = await request.json()
    items = request_data.get("items")

    user = await user_service.get_user(auth.username)
    created = await order_service.add_order(OrderReq(user_id=user.id, items=items))
    if created:
        return web.json_response({"status": "success"})
    return web.json_response({"error": "Failed to create order"}, status=500)


app = web.Application()
app.router.add_post("/api/v1/login", login)
app.router.add_get("/api/v1/profile", profile)
app.router.add_get("/api/v1/orders", get_orders)
app.router.add_post("/api/v1/orders", add_order)
