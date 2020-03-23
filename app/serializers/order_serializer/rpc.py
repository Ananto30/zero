from ..serialization_types import Etypes, type_check
from .serializer import CreateOrderReq


class SupportedOperations:
    CREATE_ORDER = 'create_order'
    GET_ORDER = 'get_order'


class CreateOrder(Etypes):
    def __init__(self, request, response=None):
        type_check(request, CreateOrderReq)
        super().__init__(SupportedOperations.CREATE_ORDER, request, response)


class GetOrder(Etypes):
    def __init__(self, request, response=None):
        super().__init__(SupportedOperations.GET_ORDER, request, response)
