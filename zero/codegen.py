import inspect


class CodeGen:
    def __init__(self, rpc_router, rpc_input_type_map, rpc_return_type_map):
        self._rpc_router = rpc_router
        self._rpc_input_type_map = rpc_input_type_map
        self._rpc_return_type_map = rpc_return_type_map
        self._typing_imports = set()

    def generate_code(self):
        code = """
import typing  # remove this if not needed
from typing import List, Dict, Union, Optional, Tuple  # remove this if not needed
from zero import ZeroClient


zero_client = ZeroClient("localhost", 5559, use_async=False)


class RpcClient:
    def __init__(self, zero_client: ZeroClient):
        self._zero_client = zero_client
        """

        for f in self._rpc_router:
            code += f"""
    def {f}(self, {self.get_function_str(f)}
        return self.zero_client.call("{f}", {None if self._rpc_input_type_map[f] is None else "msg"})
        """
        return code

    def get_imports(self):
        return f"from typing import {', '.join([i for i in self._typing_imports])}"

    def get_input_type_str(self, func_name: str):
        if self._rpc_input_type_map[func_name] is None:
            return ""
        if self._rpc_input_type_map[func_name].__module__ == "typing":
            n = self._rpc_input_type_map[func_name]._name
            self._typing_imports.add(n)
            return ": " + n
        return ": " + self._rpc_input_type_map[func_name].__name__

    def get_return_type_str(self, func_name: str):
        if self._rpc_return_type_map[func_name].__module__ == "typing":
            n = self._rpc_return_type_map[func_name]._name
            self._typing_imports.add(n)
            return n
        return self._rpc_return_type_map[func_name].__name__

    def get_function_str(self, func_name: str):
        return inspect.getsourcelines(self._rpc_router[func_name])[0][0].split("(", 1)[1].replace("\n", "")
