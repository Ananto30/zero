import logging

from app.serializers import CreateOrderReq, GetOrderReq, Etype, OrderService, Btype

from .order_handler import create_order, get_order
from app.helper import exec_time
from .logger import info

class Controller:

    # Factory of service's methods
    factory = {
        # Map methods to corresponding methods and serializers
        OrderService.CREATE_ORDER: [create_order, CreateOrderReq],
        OrderService.GET_ORDER: [get_order, GetOrderReq]
    }

    @staticmethod
    # @exec_time
    def handle_request(event: bytes):
        event_data = Etype.unpack(event)
        if event_data.operation not in Controller.factory:
            raise Exception(f"Unknown event {vars(event_data)}")
        method = Controller.factory[event_data.operation][0]
        req_class = Controller.factory[event_data.operation][1]
        event_data.request = req_class(**event_data.request)
        event_data.response = method(event_data.request)
        # info(f"Request served - {Btype.get_all_vars(event_data)}")
        print(f"Request served - {Btype.get_all_vars(event_data)}")
        return event_data.pack()
