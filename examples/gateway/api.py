import zmq
from app.serializers import *
from app.helper import exec_time

context = zmq.Context()


@exec_time
def auth_calls():
    socket = context.socket(zmq.REQ)
    # socket = context.socket(zmq.DEALER)
    socket.setsockopt(zmq.RCVTIMEO, 10000)
    socket.connect("tcp://localhost:5558")
    req = GetTokenReq("a1b2c3", "secret")
    rpc = GetToken(request=req)
    socket.send(rpc.pack())
    unpacked = Etype.unpack(socket.recv())
    # token = unpacked.response['token']
    # rpc = Authenticate(Token(token))
    # socket.send(rpc.pack())
    # unpacked = Etype.unpack(socket.recv())
    print(vars(unpacked))
    socket.close()

@exec_time
def order_calls():
    print("Connecting to order server…")
    socket = context.socket(zmq.REQ)
    socket.setsockopt(zmq.RCVTIMEO, 10000)
    socket.connect("tcp://localhost:5559")
    req = CreateOrderReq('1', ['apple', 'python'])
    event = CreateOrder(req)
    socket.send(event.pack())
    rcv = socket.recv()
    unpacked = Etype.unpack(rcv)
    print(Btype.get_all_vars(unpacked))
    req = GetOrderReq(unpacked.response['order_id'])
    event = GetOrder(req)
    socket.send(event.pack())
    print(vars(Etype.unpack(socket.recv())))


if __name__ == "__main__":
    order_calls()