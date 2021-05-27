from dataclasses import dataclass

from ..serialization_types import Etype
from .serializer import CreateOrderReq, GetOrderReq, OrderResp


class OrderService:
    CREATE_ORDER = 'create_order'
    GET_ORDER = 'get_order'


@dataclass
class CreateOrder(Etype):
    request: CreateOrderReq
    operation: str = OrderService.CREATE_ORDER
    response: OrderResp


@dataclass
class GetOrder(Etype):
    request: GetOrderReq
    operation: str = OrderService.GET_ORDER
    response: OrderResp

