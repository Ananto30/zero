from dataclasses import dataclass

from ..serialization_types import Btype


@dataclass
class CreateOrderReq(Btype):
    user_id: str
    items: list


@dataclass
class GetOrderReq(Btype):
    order_id: str


@dataclass
class OrderResp(Btype):
    order_id: str
    status: int
    items: list
