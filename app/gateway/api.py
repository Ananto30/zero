import zmq
from app.serializers import CreateOrder, GetOrder, CreateOrderReq, GetOrderReq, Etypes


context = zmq.Context()

print("Connecting to order server…")
socket = context.socket(zmq.REQ)
socket.setsockopt(zmq.RCVTIMEO, 10000)
socket.connect("tcp://localhost:6666")

req = CreateOrderReq('1', ['apple', 'python'])
event = CreateOrder(req)

socket.send(event.pack())

unpacked = Etypes.unpack(socket.recv())
print(vars(unpacked))


req = GetOrderReq(unpacked.response['order_id'])
event = GetOrder(req)

socket.send(event.pack())

print(vars(Etypes.unpack(socket.recv())))
