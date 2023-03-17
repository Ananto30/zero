import pytest
from zero import ZeroServer
from zero.errors import ZeroException


class DummyService:

    def hello(self):
        return 'world'

    def say_no(self) -> str:
        return 'no'

    def say_yes(self, please: bool = False) -> str:
        if not please:
            return "ask nicely."
        return "yes"

    @staticmethod
    def ping() -> str:
        return pong

    @classmethod
    def name(cls) -> str:
        return cls.__name__


def test_methods():
    app = ZeroServer()
    service = DummyService()
    app.register_rpc(service.say_no)
    app.register_rpc(service.say_yes)
    app.register_rpc(service.ping)
    app.register_rpc(service.name)


def test_methods_no_args():
    app = ZeroServer()
    service = DummyService()
    app.register_rpc(service.hello)
