from app.serializers.auth_serializer import GetTokenReq, Token
import jwt


def get_token(req: GetTokenReq) -> Token:
    # Static check
    if req.user_id == "a1b2c3" and req.password == "secret":
        encoded_jwt = jwt.encode({'user_id': req.user_id}, 'secret', algorithm='HS256')

        return Token(encoded_jwt)


def authenticate(req: Token) -> bool:

    # Static check
    decoded_jwt = jwt.decode(req.token, 'secret', algorithms=['HS256'])
    if 'user_id' in decoded_jwt and decoded_jwt['user_id'] == "a1b2c3":
        return True
