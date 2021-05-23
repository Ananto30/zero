from aiohttp import web
import jwt

routes = web.RouteTableDef()


class Yo:
    def __init__(self, token):
        self.token = token


@routes.get('/')
async def hello(request):

    encoded_jwt = jwt.encode({'user_id': 'a1b2c3'}, 'secret', algorithm='HS256')
    decoded_jwt = jwt.decode(encoded_jwt, 'secret', algorithms=['HS256'])
    unpacked = Yo(decoded_jwt)

    return web.Response(text=str(vars(unpacked)))


async def my_web_app():
    app = web.Application()
    app.router.add_get('/', hello)
    return app
