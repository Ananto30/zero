import datetime
import decimal
import enum
import inspect
import sys
import uuid
from dataclasses import is_dataclass
from typing import (
    Callable,
    Dict,
    List,
    Optional,
    Set,
    Tuple,
    Type,
    Union,
    get_args,
    get_origin,
    get_type_hints,
)

import msgspec

from zero.utils.type_util import typing_types

try:
    from pydantic import BaseModel

    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False

python_version = sys.version_info


class CodeGen:
    def __init__(
        self,
        rpc_router: Dict[str, Tuple[Callable, bool]],
        rpc_input_type_map: Dict[str, Optional[type]],
        rpc_return_type_map: Dict[str, Optional[type]],
    ):
        self._rpc_router = rpc_router
        self._rpc_input_type_map = rpc_input_type_map
        self._rpc_return_type_map = rpc_return_type_map

        # for imports
        self._typing_imports: List[str] = [
            str(typ).replace("typing.", "") for typ in typing_types
        ]
        self._typing_imports.sort()
        self._datetime_imports: Set[str] = set()
        self._has_uuid = False
        self._has_decimal = False
        self._has_enum = True

    def generate_code(self, host="localhost", port=5559):
        code = f"""# Generated by Zero
# import types as per needed, not all imports are shown here

from zero import ZeroClient


zero_client = ZeroClient("{host}", {port})

"""
        code += self.generate_models()
        code += """
class RpcClient:
    def __init__(self, zero_client: ZeroClient):
        self._zero_client = zero_client
"""

        for func_name in self._rpc_router:
            input_param_name = (
                None
                if self._rpc_input_type_map[func_name] is None
                else self.get_function_input_param_name(func_name)
            )
            code += f"""
    {self.get_function_str(func_name)}
        return self._zero_client.call("{func_name}", {input_param_name})
"""

        # add imports after first 2 lines
        code_lines = code.split("\n")
        code_lines.insert(2, self.get_imports(code))
        code = "\n".join(code_lines)

        if "typing." in code:
            code = code.replace("typing.", "")
        if "@dataclasses.dataclass" in code:
            code = code.replace("@dataclasses.dataclass", "@dataclass")
        if "datetime.datetime" in code:
            code = code.replace("datetime.datetime", "datetime")
        if "datetime.date" in code:
            code = code.replace("datetime.date", "date")
        if "datetime.time" in code:
            code = code.replace("datetime.time", "time")

        return code

    def get_imports(self, code):
        for func_name in self._rpc_input_type_map:
            input_type = self._rpc_input_type_map[func_name]
            self._track_imports(input_type)

        for typ in list(self._typing_imports):
            if typ + "[" not in code:
                self._typing_imports.remove(typ)

        import_lines = []

        if "@dataclasses.dataclass" in code or "@dataclass" in code:
            import_lines.append("from dataclasses import dataclass")

        if self._datetime_imports:
            import_lines.append(
                "from datetime import " + ", ".join(sorted(self._datetime_imports))
            )

        if self._has_decimal:
            import_lines.append("import decimal")
        if self._has_enum:
            import_lines.append("import enum")

        if "(msgspec.Struct)" in code:
            import_lines.append("import msgspec")

        if "(Struct)" in code:
            import_lines.append("from msgspec import Struct")

        if "(BaseModel)" in code:
            import_lines.append("from pydantic import BaseModel")

        if self._typing_imports:
            import_lines.append("from typing import " + ", ".join(self._typing_imports))

        if self._has_uuid:
            import_lines.append("import uuid")

        return "\n".join(import_lines)

    def _track_imports(self, input_type):
        if not input_type:
            return
        if input_type in (datetime.datetime, datetime.date, datetime.time):
            self._datetime_imports.add(input_type.__name__)
        elif input_type == uuid.UUID:
            self._has_uuid = True
        elif input_type == decimal.Decimal:
            self._has_decimal = True

    def get_function_str(self, func_name: str):
        func = self._rpc_router[func_name][0]
        func_lines = inspect.getsourcelines(func)[0]
        func_str = "".join(func_lines)
        # from def to ->
        def_str = func_str.split("def")[1].split("->")[0].strip()
        def_str = "def " + def_str

        # Insert 'self' as the first parameter
        insert_index = def_str.index("(") + 1
        if self._rpc_input_type_map[func_name]:  # If there is input, add 'self, '
            def_str = def_str[:insert_index] + "self, " + def_str[insert_index:]
        else:  # If there is no input, just add 'self'
            def_str = def_str[:insert_index] + "self" + def_str[insert_index:]

        # from -> to :
        return_type_str = func_str.split("->")[1].split(":")[0].strip()
        # add return type
        def_str = def_str + f" -> {return_type_str}:"

        return def_str.strip()

    def get_function_input_param_name(self, func_name: str):
        func = self._rpc_router[func_name][0]
        func_lines = inspect.getsourcelines(func)[0]
        func_str = "".join(func_lines)
        # from bracket to bracket
        input_param_name = func_str.split("(")[1].split(")")[0]
        # everything until :
        input_param_name = input_param_name.split(":")[0]
        return input_param_name.strip()

    def _generate_class_code(self, cls: Type, already_generated: Set[Type]) -> str:
        if cls in already_generated:
            return ""

        code = self._generate_code_for_bases(cls, already_generated)
        code += self._generate_code_for_fields(cls, already_generated)

        if python_version >= (3, 9):
            code += inspect.getsource(cls) + "\n\n"
        else:  # pragma: no cover
            #  python 3.8 doesnt return @dataclass decorator
            if is_dataclass(cls):
                code += f"@dataclass\n{inspect.getsource(cls)}\n\n"
            else:
                code += inspect.getsource(cls) + "\n\n"

        already_generated.add(cls)
        return code

    def _generate_code_for_bases(self, cls: Type, already_generated: Set[Type]) -> str:
        code = ""
        for base_cls in cls.__bases__:
            if issubclass(base_cls, msgspec.Struct) and base_cls is not msgspec.Struct:
                code += self._generate_class_code(base_cls, already_generated)
            elif is_dataclass(base_cls):
                code += self._generate_class_code(base_cls, already_generated)
        return code

    def _generate_code_for_fields(self, cls: Type, already_generated: Set[Type]) -> str:
        code = ""
        for field_type in get_type_hints(cls).values():
            code += self._generate_code_for_type(field_type, already_generated)
        return code

    def _generate_code_for_type(self, typ: Type, already_generated: Set[Type]) -> str:
        code = ""
        all_possible_typs = self._resolve_field_type(typ)
        for possible_typ in all_possible_typs:
            self._track_imports(possible_typ)
            if isinstance(possible_typ, type) and (
                issubclass(possible_typ, (msgspec.Struct, enum.Enum, enum.IntEnum))
                or is_dataclass(possible_typ)
                or (
                    PYDANTIC_AVAILABLE
                    and issubclass(  # pytype: disable=wrong-arg-types
                        possible_typ, BaseModel
                    )
                )
            ):
                code += self._generate_class_code(possible_typ, already_generated)
        return code

    def _resolve_field_type(self, field_type) -> List[Type]:
        origin = get_origin(field_type)
        if origin in (list, tuple, set, frozenset, Optional):
            return [get_args(field_type)[0]]
        if origin == dict:
            return [get_args(field_type)[1]]
        if origin == Union:
            return list(get_args(field_type))

        return [field_type]

    def generate_models(self) -> str:
        already_generated: Set[Type] = set()
        code = ""

        merged_types = list(self._rpc_input_type_map.values()) + list(
            self._rpc_return_type_map.values()
        )
        # retain order and remove duplicates
        merged_types = list(dict.fromkeys(merged_types))

        for input_type in merged_types:
            if input_type is None:
                continue
            code += self._generate_code_for_type(input_type, already_generated)

        return code
