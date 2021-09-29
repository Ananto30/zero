import os.path

from zero.generate_client import generate_client_code_and_save


def test_codegeneration():
    generate_client_code_and_save("localhost", 5559, ".", overwrite_dir=True)
    assert os.path.isfile("rpc_client.py")
    with open("rpc_client.py") as f:
        code = f.read()
        print(code)
        assert (
            code
            == """
import typing  # remove this if not needed
from typing import List, Dict, Union, Optional, Tuple  # remove this if not needed
from zero import ZeroClient


zero_client = ZeroClient("localhost", 5559, use_async=False)


class RpcClient:
    def __init__(self, zero_client: ZeroClient):
        self._zero_client = zero_client
        
    def echo(self, msg: str) -> str:
        return self.zero_client.call("echo", msg)
        
    def hello_world(self, ) -> str:
        return self.zero_client.call("hello_world", None)
        
    def decode_jwt(self, msg: str) -> str:
        return self.zero_client.call("decode_jwt", msg)
        
    def sum_list(self, msg: typing.List[int]) -> int:
        return self.zero_client.call("sum_list", msg)
        
    def echo_dict(self, msg: typing.Dict[int, str]) -> typing.Dict[int, str]:
        return self.zero_client.call("echo_dict", msg)
        
    def echo_tuple(self, msg: typing.Tuple[int, str]) -> typing.Tuple[int, str]:
        return self.zero_client.call("echo_tuple", msg)
        
    def echo_union(self, msg: typing.Union[int, str]) -> typing.Union[int, str]:
        return self.zero_client.call("echo_union", msg)
        """
        )

    os.remove("rpc_client.py")
