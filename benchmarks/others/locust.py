import time

from locust import User, events, task

from zero import ZeroClient


class ZeroMqClient(object):
    def __init__(self, zero_client):
        self.zero_client = zero_client

    def send(self, event):
        start_time = time.time()
        try:
            result = self.zero_client.call("hello_world", "")

        except Exception as e:
            total_time = int((time.time() - start_time) * 1000)
            events.request_failure.fire(
                request_type="send",
                name=event,
                response_time=total_time,
                exception=e,
                response_length=0,
            )
        else:
            total_time = int((time.time() - start_time) * 1000)
            length = len(result)
            events.request_success.fire(
                request_type="send",
                name=event,
                response_time=total_time,
                response_length=length,
            )

        # return result


class ZeroMqLocust(User):
    client = None
    abstract = True

    def __init__(self, *args, **kwargs):
        super(ZeroMqLocust, self).__init__(*args, **kwargs)

        zero_client = ZeroClient("localhost", "5559")

        self.client = ZeroMqClient(zero_client)


class WebsiteUser(ZeroMqLocust):
    min_wait = 1
    max_wait = 3

    @task
    def hello_world(self):
        self.client.send("hello_world")
