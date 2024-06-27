import dataclasses
import datetime
import decimal
import enum
import typing
import unittest
import uuid
from dataclasses import dataclass
from datetime import date
from typing import Dict, List, Optional, Tuple, Union

import msgspec
from msgspec import Struct

from zero.codegen.codegen import CodeGen


@dataclass
class SimpleDataclass:
    a: int
    b: str


@dataclasses.dataclass
class SimpleDataclass2:
    c: int
    d: str


@dataclass
class ChildDataclass(SimpleDataclass):
    e: int
    f: str


class SimpleStruct(Struct):
    h: int
    i: str


class ComplexStruct(msgspec.Struct):
    a: int
    b: str
    c: SimpleStruct
    d: List[SimpleStruct]
    e: Dict[str, SimpleStruct]
    f: Tuple[SimpleDataclass, SimpleStruct]
    g: Union[SimpleStruct, SimpleDataclass, SimpleDataclass2]


class ChildComplexStruct(ComplexStruct):
    h: int
    i: str


class SimpleEnum(enum.Enum):
    ONE = 1
    TWO = 2


class SimpleIntEnum(enum.IntEnum):
    ONE = 1
    TWO = 2


def func_none(arg: None) -> str:
    return "Received None"


def func_bool(arg: bool) -> str:
    return f"Received bool: {arg}"


def func_int(arg: int) -> str:
    return f"Received int: {arg}"


def func_float(arg: float) -> str:
    return f"Received float: {arg}"


def func_str(arg: str) -> str:
    return f"Received str: {arg}"


def func_bytes(arg: bytes) -> str:
    return f"Received bytes: {arg}"


def func_bytearray(arg: bytearray) -> str:
    return f"Received bytearray: {arg}"


def func_tuple(arg: tuple) -> str:
    return f"Received tuple: {arg}"


def func_list(arg: list) -> str:
    return f"Received list: {arg}"


def func_dict(arg: dict) -> str:
    return f"Received dict: {arg}"


def func_optional_dict(arg: Optional[dict]) -> str:
    return f"Received dict: {arg}"


def func_set(arg: set) -> str:
    return f"Received set: {arg}"


def func_frozenset(arg: frozenset) -> str:
    return f"Received frozenset: {arg}"


def func_datetime(arg: datetime.datetime) -> str:
    return f"Received datetime: {arg}"


def func_date(arg: date) -> str:
    return f"Received date: {arg}"


def func_time(arg: datetime.time) -> str:
    return f"Received time: {arg}"


def func_uuid(arg: uuid.UUID) -> str:
    return f"Received UUID: {arg}"


def func_decimal(arg: decimal.Decimal) -> str:
    return f"Received Decimal: {arg}"


def func_enum(arg: SimpleEnum) -> str:
    return f"Received Enum: {arg}"


def func_intenum(arg: SimpleIntEnum) -> str:
    return f"Received IntEnum: {arg}"


def func_dataclass(arg: SimpleDataclass) -> str:
    return f"Received dataclass: {arg}"


def func_tuple_typing(arg: typing.Tuple[int, str]) -> str:
    return f"Received typing.Tuple: {arg}"


def func_list_typing(arg: typing.List[int]) -> str:
    return f"Received typing.List: {arg}"


def func_dict_typing(arg: typing.Dict[str, int]) -> str:
    return f"Received typing.Dict: {arg}"


def func_set_typing(arg: typing.Set[int]) -> str:
    return f"Received typing.Set: {arg}"


def func_frozenset_typing(arg: typing.FrozenSet[int]) -> str:
    return f"Received typing.FrozenSet: {arg}"


def func_any_typing(arg: typing.Any) -> str:
    return f"Received typing.Any: {arg}"


def func_union_typing(arg: typing.Union[int, str]) -> str:
    return f"Received typing.Union: {arg}"


def func_optional_typing(arg: typing.Optional[int]) -> str:
    return f"Received typing.Optional: {arg}"


def func_msgspec_struct(arg: SimpleStruct) -> str:
    return f"Received msgspec.Struct: {arg}"


def func_msgspec_struct_complex(arg: ComplexStruct) -> str:
    return f"Received msgspec.Struct: {arg}"


def func_child_complex_struct(arg: ChildComplexStruct) -> str:
    return f"Received msgspec.Struct: {arg}"


def func_return_optional_child_complex_struct() -> Optional[ChildComplexStruct]:
    return None


def func_return_complex_struct() -> ComplexStruct:
    return ComplexStruct(
        a=1,
        b="hello",
        c=SimpleStruct(h=1, i="hello"),
        d=[SimpleStruct(h=1, i="hello")],
        e={"1": SimpleStruct(h=1, i="hello")},
        f=(SimpleDataclass(a=1, b="hello"), SimpleStruct(h=1, i="hello")),
        g=SimpleDataclass(a=1, b="hello"),
    )


def func_take_optional_child_dataclass_return_optional_child_complex_struct(
    arg: Optional[ChildDataclass],
) -> Optional[ChildComplexStruct]:
    return None


class TestCodegen(unittest.TestCase):
    def setUp(self) -> None:
        self.maxDiff = None
        self._rpc_router = {
            "func_none": (func_none, False),
            "func_bool": (func_bool, False),
            "func_int": (func_int, False),
            "func_float": (func_float, False),
            "func_str": (func_str, False),
            "func_bytes": (func_bytes, False),
            "func_bytearray": (func_bytearray, False),
            "func_tuple": (func_tuple, False),
            "func_list": (func_list, False),
            "func_dict": (func_dict, False),
            "func_optional_dict": (func_optional_dict, False),
            "func_set": (func_set, False),
            "func_frozenset": (func_frozenset, False),
            "func_datetime": (func_datetime, False),
            "func_date": (func_date, False),
            "func_time": (func_time, False),
            "func_uuid": (func_uuid, False),
            "func_decimal": (func_decimal, False),
            "func_enum": (func_enum, False),
            "func_intenum": (func_intenum, False),
            "func_dataclass": (func_dataclass, False),
            "func_tuple_typing": (func_tuple_typing, False),
            "func_list_typing": (func_list_typing, False),
            "func_dict_typing": (func_dict_typing, False),
            "func_set_typing": (func_set_typing, False),
            "func_frozenset_typing": (func_frozenset_typing, False),
            "func_any_typing": (func_any_typing, False),
            "func_union_typing": (func_union_typing, False),
            "func_optional_typing": (func_optional_typing, False),
            "func_msgspec_struct": (func_msgspec_struct, False),
            "func_msgspec_struct_complex": (func_msgspec_struct_complex, False),
            "func_child_complex_struct": (func_child_complex_struct, False),
            "func_return_complex_struct": (func_return_complex_struct, False),
        }
        self._rpc_input_type_map = {
            "func_none": None,
            "func_bool": bool,
            "func_int": int,
            "func_float": float,
            "func_str": str,
            "func_bytes": bytes,
            "func_bytearray": bytearray,
            "func_tuple": tuple,
            "func_list": list,
            "func_dict": dict,
            "func_optional_dict": Optional[dict],
            "func_set": set,
            "func_frozenset": frozenset,
            "func_datetime": datetime.datetime,
            "func_date": datetime.date,
            "func_time": datetime.time,
            "func_uuid": uuid.UUID,
            "func_decimal": decimal.Decimal,
            "func_enum": SimpleEnum,
            "func_intenum": SimpleIntEnum,
            "func_dataclass": SimpleDataclass,
            "func_tuple_typing": typing.Tuple[int, str],
            "func_list_typing": typing.List[int],
            "func_dict_typing": typing.Dict[str, int],
            "func_set_typing": typing.Set[int],
            "func_frozenset_typing": typing.FrozenSet[int],
            "func_any_typing": typing.Any,
            "func_union_typing": typing.Union[int, str],
            "func_optional_typing": typing.Optional[int],
            "func_msgspec_struct": SimpleStruct,
            "func_msgspec_struct_complex": ComplexStruct,
            "func_child_complex_struct": ChildComplexStruct,
            "func_return_complex_struct": None,
        }
        self._rpc_return_type_map = {
            "func_none": str,
            "func_bool": str,
            "func_int": str,
            "func_float": str,
            "func_str": str,
            "func_bytes": str,
            "func_bytearray": str,
            "func_tuple": str,
            "func_list": str,
            "func_dict": str,
            "func_optional_dict": Optional[str],
            "func_set": str,
            "func_frozenset": str,
            "func_datetime": str,
            "func_date": str,
            "func_time": str,
            "func_uuid": str,
            "func_decimal": str,
            "func_enum": str,
            "func_intenum": str,
            "func_dataclass": str,
            "func_tuple_typing": str,
            "func_list_typing": str,
            "func_dict_typing": str,
            "func_set_typing": str,
            "func_frozenset_typing": str,
            "func_any_typing": str,
            "func_union_typing": str,
            "func_optional_typing": str,
            "func_msgspec_struct": str,
            "func_msgspec_struct_complex": str,
            "func_child_complex_struct": str,
            "func_return_complex_struct": ComplexStruct,
        }

    def test_codegen(self):
        codegen = CodeGen(
            self._rpc_router, self._rpc_input_type_map, self._rpc_return_type_map
        )
        code = codegen.generate_code()
        expected_code = """# Generated by Zero
# import types as per needed, not all imports are shown here
from dataclasses import dataclass
from datetime import date, datetime, time
import decimal
import enum
import msgspec
from msgspec import Struct
from typing import Dict, FrozenSet, List, Optional, Set, Tuple, Union
import uuid

from zero import ZeroClient


zero_client = ZeroClient("localhost", 5559)

class SimpleEnum(enum.Enum):
    ONE = 1
    TWO = 2


class SimpleIntEnum(enum.IntEnum):
    ONE = 1
    TWO = 2


@dataclass
class SimpleDataclass:
    a: int
    b: str


class SimpleStruct(Struct):
    h: int
    i: str


@dataclass
class SimpleDataclass2:
    c: int
    d: str


class ComplexStruct(msgspec.Struct):
    a: int
    b: str
    c: SimpleStruct
    d: List[SimpleStruct]
    e: Dict[str, SimpleStruct]
    f: Tuple[SimpleDataclass, SimpleStruct]
    g: Union[SimpleStruct, SimpleDataclass, SimpleDataclass2]


class ChildComplexStruct(ComplexStruct):
    h: int
    i: str



class RpcClient:
    def __init__(self, zero_client: ZeroClient):
        self._zero_client = zero_client

    def func_none(selfarg: None) -> str:
        return self._zero_client.call("func_none", None)

    def func_bool(self, arg: bool) -> str:
        return self._zero_client.call("func_bool", arg)

    def func_int(self, arg: int) -> str:
        return self._zero_client.call("func_int", arg)

    def func_float(self, arg: float) -> str:
        return self._zero_client.call("func_float", arg)

    def func_str(self, arg: str) -> str:
        return self._zero_client.call("func_str", arg)

    def func_bytes(self, arg: bytes) -> str:
        return self._zero_client.call("func_bytes", arg)

    def func_bytearray(self, arg: bytearray) -> str:
        return self._zero_client.call("func_bytearray", arg)

    def func_tuple(self, arg: tuple) -> str:
        return self._zero_client.call("func_tuple", arg)

    def func_list(self, arg: list) -> str:
        return self._zero_client.call("func_list", arg)

    def func_dict(self, arg: dict) -> str:
        return self._zero_client.call("func_dict", arg)

    def func_optional_dict(self, arg: Optional[dict]) -> str:
        return self._zero_client.call("func_optional_dict", arg)

    def func_set(self, arg: set) -> str:
        return self._zero_client.call("func_set", arg)

    def func_frozenset(self, arg: frozenset) -> str:
        return self._zero_client.call("func_frozenset", arg)

    def func_datetime(self, arg: datetime) -> str:
        return self._zero_client.call("func_datetime", arg)

    def func_date(self, arg: date) -> str:
        return self._zero_client.call("func_date", arg)

    def func_time(self, arg: time) -> str:
        return self._zero_client.call("func_time", arg)

    def func_uuid(self, arg: uuid.UUID) -> str:
        return self._zero_client.call("func_uuid", arg)

    def func_decimal(self, arg: decimal.Decimal) -> str:
        return self._zero_client.call("func_decimal", arg)

    def func_enum(self, arg: SimpleEnum) -> str:
        return self._zero_client.call("func_enum", arg)

    def func_intenum(self, arg: SimpleIntEnum) -> str:
        return self._zero_client.call("func_intenum", arg)

    def func_dataclass(self, arg: SimpleDataclass) -> str:
        return self._zero_client.call("func_dataclass", arg)

    def func_tuple_typing(self, arg: Tuple[int, str]) -> str:
        return self._zero_client.call("func_tuple_typing", arg)

    def func_list_typing(self, arg: List[int]) -> str:
        return self._zero_client.call("func_list_typing", arg)

    def func_dict_typing(self, arg: Dict[str, int]) -> str:
        return self._zero_client.call("func_dict_typing", arg)

    def func_set_typing(self, arg: Set[int]) -> str:
        return self._zero_client.call("func_set_typing", arg)

    def func_frozenset_typing(self, arg: FrozenSet[int]) -> str:
        return self._zero_client.call("func_frozenset_typing", arg)

    def func_any_typing(self, arg: Any) -> str:
        return self._zero_client.call("func_any_typing", arg)

    def func_union_typing(self, arg: Union[int, str]) -> str:
        return self._zero_client.call("func_union_typing", arg)

    def func_optional_typing(self, arg: Optional[int]) -> str:
        return self._zero_client.call("func_optional_typing", arg)

    def func_msgspec_struct(self, arg: SimpleStruct) -> str:
        return self._zero_client.call("func_msgspec_struct", arg)

    def func_msgspec_struct_complex(self, arg: ComplexStruct) -> str:
        return self._zero_client.call("func_msgspec_struct_complex", arg)

    def func_child_complex_struct(self, arg: ChildComplexStruct) -> str:
        return self._zero_client.call("func_child_complex_struct", arg)

    def func_return_complex_struct(self) -> ComplexStruct:
        return self._zero_client.call("func_return_complex_struct", None)
"""
        self.assertEqual(code, expected_code)

    def test_codegen_return_single_complex_struct(self):
        rpc_router = {
            "func_return_complex_struct": (func_return_complex_struct, False),
        }
        rpc_input_type_map = {
            "func_return_complex_struct": None,
        }
        rpc_return_type_map = {
            "func_return_complex_struct": ComplexStruct,
        }
        codegen = CodeGen(rpc_router, rpc_input_type_map, rpc_return_type_map)
        code = codegen.generate_code()
        expected_code = """# Generated by Zero
# import types as per needed, not all imports are shown here
from dataclasses import dataclass
import enum
import msgspec
from msgspec import Struct
from typing import Dict, List, Tuple, Union

from zero import ZeroClient


zero_client = ZeroClient("localhost", 5559)

class SimpleStruct(Struct):
    h: int
    i: str


@dataclass
class SimpleDataclass:
    a: int
    b: str


@dataclass
class SimpleDataclass2:
    c: int
    d: str


class ComplexStruct(msgspec.Struct):
    a: int
    b: str
    c: SimpleStruct
    d: List[SimpleStruct]
    e: Dict[str, SimpleStruct]
    f: Tuple[SimpleDataclass, SimpleStruct]
    g: Union[SimpleStruct, SimpleDataclass, SimpleDataclass2]



class RpcClient:
    def __init__(self, zero_client: ZeroClient):
        self._zero_client = zero_client

    def func_return_complex_struct(self) -> ComplexStruct:
        return self._zero_client.call("func_return_complex_struct", None)
"""
        self.assertEqual(code, expected_code)

    def test_codegen_return_optional_complex_struct(self):
        rpc_router = {
            "func_return_optional_child_complex_struct": (
                func_return_optional_child_complex_struct,
                False,
            ),
        }
        rpc_input_type_map = {
            "func_return_optional_child_complex_struct": None,
        }
        rpc_return_type_map = {
            "func_return_optional_child_complex_struct": Optional[ChildComplexStruct],
        }
        codegen = CodeGen(rpc_router, rpc_input_type_map, rpc_return_type_map)
        code = codegen.generate_code()
        expected_code = """# Generated by Zero
# import types as per needed, not all imports are shown here
from dataclasses import dataclass
import enum
import msgspec
from msgspec import Struct
from typing import Dict, List, Optional, Tuple, Union

from zero import ZeroClient


zero_client = ZeroClient("localhost", 5559)

class SimpleStruct(Struct):
    h: int
    i: str


@dataclass
class SimpleDataclass:
    a: int
    b: str


@dataclass
class SimpleDataclass2:
    c: int
    d: str


class ComplexStruct(msgspec.Struct):
    a: int
    b: str
    c: SimpleStruct
    d: List[SimpleStruct]
    e: Dict[str, SimpleStruct]
    f: Tuple[SimpleDataclass, SimpleStruct]
    g: Union[SimpleStruct, SimpleDataclass, SimpleDataclass2]


class ChildComplexStruct(ComplexStruct):
    h: int
    i: str



class RpcClient:
    def __init__(self, zero_client: ZeroClient):
        self._zero_client = zero_client

    def func_return_optional_child_complex_struct(self) -> Optional[ChildComplexStruct]:
        return self._zero_client.call("func_return_optional_child_complex_struct", None)
"""
        self.assertEqual(code, expected_code)

    def test_codegen_optional_child_dataclass_return_optional_child_complex_struct(
        self,
    ):
        rpc_router = {
            "func_take_optional_child_dataclass_return_optional_child_complex_struct": (
                func_take_optional_child_dataclass_return_optional_child_complex_struct,
                False,
            ),
        }
        rpc_input_type_map = {
            "func_take_optional_child_dataclass_return_optional_child_complex_struct": Optional[
                ChildDataclass
            ],
        }
        rpc_return_type_map = {
            "func_take_optional_child_dataclass_return_optional_child_complex_struct": Optional[
                ChildComplexStruct
            ],
        }
        codegen = CodeGen(rpc_router, rpc_input_type_map, rpc_return_type_map)
        code = codegen.generate_code()
        expected_code = """# Generated by Zero
# import types as per needed, not all imports are shown here
from dataclasses import dataclass
import enum
import msgspec
from msgspec import Struct
from typing import Dict, List, Optional, Tuple, Union

from zero import ZeroClient


zero_client = ZeroClient("localhost", 5559)

@dataclass
class SimpleDataclass:
    a: int
    b: str


@dataclass
class ChildDataclass(SimpleDataclass):
    e: int
    f: str


class SimpleStruct(Struct):
    h: int
    i: str


@dataclass
class SimpleDataclass2:
    c: int
    d: str


class ComplexStruct(msgspec.Struct):
    a: int
    b: str
    c: SimpleStruct
    d: List[SimpleStruct]
    e: Dict[str, SimpleStruct]
    f: Tuple[SimpleDataclass, SimpleStruct]
    g: Union[SimpleStruct, SimpleDataclass, SimpleDataclass2]


class ChildComplexStruct(ComplexStruct):
    h: int
    i: str



class RpcClient:
    def __init__(self, zero_client: ZeroClient):
        self._zero_client = zero_client

    def func_take_optional_child_dataclass_return_optional_child_complex_struct(self, 
    arg: Optional[ChildDataclass],
) -> Optional[ChildComplexStruct]:
        return self._zero_client.call("func_take_optional_child_dataclass_return_optional_child_complex_struct", arg)
"""
        self.assertEqual(code, expected_code)
