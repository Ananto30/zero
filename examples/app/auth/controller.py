import logging

from app.serializers import AuthOperations, Btype, Etype, GetTokenReq, Token

from .auth_handler import authenticate, get_token
from app.helper import exec_time

class Controller:

    # Factory of operations
    factory = {
        # Map operations to corresponding methods and serializers
        AuthOperations.GET_TOKEN: [get_token, GetTokenReq],
        AuthOperations.AUTHENTICATE: [authenticate, Token]
    }

    @staticmethod
    @exec_time
    def handle_request(event: bytes):
        event_data = Etype.unpack(event)
        if event_data.operation not in Controller.factory:
            raise Exception(f"Unknown event {vars(event_data)}")
        method = Controller.factory[event_data.operation][0]
        req_class = Controller.factory[event_data.operation][1]
        event_data.request = req_class(**event_data.request)
        event_data.response = method(event_data.request)
        event_data_vars = Btype.get_all_vars(event_data)
        logging.info(f"Request served - {event_data_vars}")
        return event_data.pack()
