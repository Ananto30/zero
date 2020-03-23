from locust import TaskSet, task, between, Locust, events
import zmq
import time
from app.serializers import CreateOrder, GetOrder, CreateOrderReq, GetOrderReq, Etypes, Btypes


class UserBehaviour(TaskSet):

    @task(1)
    def create_order(self):
        req = CreateOrderReq('1', ['apple', 'python'])
        event = CreateOrder(req)
        self.client.send(event.pack(), event.operation)

    # @task(1)
    # def profile(self):
    #     self.client.get("/profile")


class ZeroMqClient(object):
    def __init__(self):
        print("Connecting to order server…")
        context = zmq.Context()
        self.socket = context.socket(zmq.REQ)
        self.socket.setsockopt(zmq.RCVTIMEO, 10000)
        self.socket.connect("tcp://localhost:5559")

    def send(self, req, operation):
        result = None
        start_time = time.time()
        try:
            self.socket.send(req)
            result = self.socket.recv()
            if not result:
                result = ''
        except Exception as e:
            total_time = int((time.time() - start_time) * 1000)
            events.request_failure.fire(request_type="send", name=operation, response_time=total_time, exception=e)
        else:
            total_time = int((time.time() - start_time) * 1000)
            length = len(result)
            events.request_success.fire(request_type="send", name=operation, response_time=total_time, response_length=length)
        return result


class ZeroMqLocust(Locust):
    def __init__(self, *args, **kwargs):
        super(ZeroMqLocust, self).__init__(*args, **kwargs)
        self.client = ZeroMqClient()
        self.key = 'key1'
        self.value = 'value1'


class WebsiteUser(ZeroMqLocust):
    task_set = UserBehaviour
    wait_time = between(5, 9)
