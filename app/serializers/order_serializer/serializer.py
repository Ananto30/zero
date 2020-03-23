from ..serialization_types import Btypes


class CreateOrderReq(Btypes):
    def __init__(self, user_id: str, items: list):
        self.user_id = user_id
        self.items = items


class GetOrderReq(Btypes):
    def __init__(self, order_id: str):
        self.order_id = order_id


class OrderResp(Btypes):
    def __init__(self, order_id: str, status: int, items: list):
        self.order_id = order_id
        self.status = status
        self.items = items

# req = CreateOrderReq('1', ['apple', 'python'])
# event = CreateOrderEvent(req)
# packed = event.pack()
# print(packed)
# print(vars(Etypes.unpack(packed)))
