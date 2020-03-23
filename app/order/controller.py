import logging

from app.serializers import CreateOrderReq, GetOrderReq, Etypes, SupportedOperations

from .order_handler import create_order, get_order


class Controller:

    # Factory of operations
    factory = {
        # Map operations to corresponding methods and serializers
        SupportedOperations.CREATE_ORDER: [create_order, CreateOrderReq],
        SupportedOperations.GET_ORDER: [get_order, GetOrderReq]
    }

    @staticmethod
    def handle_request(event: bin):
        event_data = Etypes.unpack(event)
        if event_data.operation not in Controller.factory:
            raise Exception(f"Unknown event {vars(event_data)}")
        method = Controller.factory[event_data.operation][0]
        req_class = Controller.factory[event_data.operation][1]
        event_data.request = req_class.unpack(event_data.request)
        event_data.response = method(event_data.request)
        logging.info(f"Request served - {event_data.get_all_vars()}")
        return event_data.pack()
