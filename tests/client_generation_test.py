import os.path

from zero.generate_client import generate_client_code_and_save


def test_codegeneration():
    generate_client_code_and_save("localhost", 5559, ".", overwrite_dir=True)
    assert os.path.isfile("rpc_client.py")
    with open("rpc_client.py") as f:
        code = f.read()
        assert (
            code
            == """
import typing  # remove this if not needed
from typing import List, Dict, Union, Optional, Tuple  # remove this if not needed
from zero import ZeroClient


zero_client = ZeroClient("localhost", 5559)


class RpcClient:
    def __init__(self, zero_client: ZeroClient):
        self._zero_client = zero_client
        
    def echo(self, msg: str) -> str:
        return self._zero_client.call("echo", msg)
        
    def hello_world(self, ) -> str:
        return self._zero_client.call("hello_world", None)
        
    def decode_jwt(self, msg: str) -> str:
        return self._zero_client.call("decode_jwt", msg)
        
    def sum_list(self, msg: typing.List[int]) -> int:
        return self._zero_client.call("sum_list", msg)
        
    def echo_dict(self, msg: typing.Dict[int, str]) -> typing.Dict[int, str]:
        return self._zero_client.call("echo_dict", msg)
        
    def echo_tuple(self, msg: typing.Tuple[int, str]) -> typing.Tuple[int, str]:
        return self._zero_client.call("echo_tuple", msg)
        
    def echo_union(self, msg: typing.Union[int, str]) -> typing.Union[int, str]:
        return self._zero_client.call("echo_union", msg)
        """
        )

    os.remove("rpc_client.py")


def test_connection_fail_in_code_generation():
    generate_client_code_and_save("localhost", 5558, ".", overwrite_dir=True)
    assert os.path.isfile("rpc_client.py") is False


def test_generate_code_in_different_directory():
    generate_client_code_and_save("localhost", 5559, "./test_codegen", overwrite_dir=True)
    assert os.path.isfile("./test_codegen/rpc_client.py")

    os.remove("./test_codegen/rpc_client.py")
    os.rmdir("./test_codegen")


def test_overwrite_dir_false(monkeypatch):
    generate_client_code_and_save("localhost", 5559, "./test_codegen", overwrite_dir=True)
    file_hash = hash(open("./test_codegen/rpc_client.py").read())

    monkeypatch.setattr("builtins.input", lambda _: "N")
    generate_client_code_and_save("localhost", 5559, "./test_codegen", overwrite_dir=False)
    assert file_hash == hash(open("./test_codegen/rpc_client.py").read())

    os.remove("./test_codegen/rpc_client.py")
    os.rmdir("./test_codegen")
