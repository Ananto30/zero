import dataclasses
import datetime
import decimal
import enum
import typing
import uuid
from typing import (
    Any,
    Callable,
    ClassVar,
    Dict,
    Optional,
    Protocol,
    Type,
    Union,
    get_origin,
    get_type_hints,
)

import msgspec

builtin_types: typing.List = [
    None,
    bool,
    int,
    float,
    str,
    bytes,
    bytearray,
    tuple,
    list,
    dict,
    set,
    frozenset,
]

std_lib_types: typing.List = [
    datetime.datetime,
    datetime.date,
    datetime.time,
    uuid.UUID,
    decimal.Decimal,
    enum.Enum,
    enum.IntEnum,
    dataclasses.dataclass,
]

typing_types: typing.List = [
    typing.Tuple,
    typing.List,
    typing.Dict,
    typing.Set,
    typing.FrozenSet,
    typing.Union,
    typing.Optional,
]

msgspec_types: typing.List = [
    msgspec.Struct,
]


allowed_types = builtin_types + std_lib_types + typing_types


class IsDataclass(Protocol):
    # as already noted in comments, checking for this attribute is currently
    # the most reliable way to ascertain that something is a dataclass
    __dataclass_fields__: ClassVar[Dict[str, Any]]


AllowedType = Union[
    None,
    bool,
    int,
    float,
    str,
    bytes,
    bytearray,
    tuple,
    list,
    dict,
    set,
    frozenset,
    datetime.datetime,
    datetime.date,
    datetime.time,
    uuid.UUID,
    decimal.Decimal,
    enum.Enum,
    enum.IntEnum,
    IsDataclass,
    typing.Tuple,
    typing.List,
    typing.Dict,
    typing.Set,
    typing.FrozenSet,
    msgspec.Struct,
    Type[enum.Enum],  # For enum classes
    Type[enum.IntEnum],  # For int enum classes
]


def verify_function_args(func: Callable) -> None:
    arg_count = func.__code__.co_argcount
    if arg_count < 1:
        return
    if arg_count > 1:
        raise ValueError(
            f"`{func.__name__}` has more than 1 args; "
            "RPC functions can have only one arg - msg, or no arg"
        )

    arg_name = func.__code__.co_varnames[0]
    func_arg_type = get_type_hints(func)
    if arg_name not in func_arg_type:
        raise TypeError(
            f"`{func.__name__}` has no type hinting; RPC functions must have type hints"
        )


def verify_function_return(func: Callable) -> None:
    types = get_type_hints(func)
    if not types.get("return"):
        raise TypeError(
            f"`{func.__name__}` has no return type hinting; RPC functions must have type hints"
        )


def get_function_input_class(func: Callable) -> Optional[type]:
    arg_count = func.__code__.co_argcount
    if arg_count == 0:
        return None
    if arg_count == 1:
        arg_name = func.__code__.co_varnames[0]
        func_arg_type = get_type_hints(func)
        return func_arg_type[arg_name]

    return None


def get_function_return_class(func: Callable):
    types = get_type_hints(func)
    return types.get("return")


def verify_function_input_type(func: Callable):
    input_type = get_function_input_class(func)
    if input_type is None:
        return

    if is_allowed_type(input_type):
        return

    raise TypeError(
        f"{func.__name__} has type {input_type} which is not allowed; "
        "allowed types are: \n" + "\n".join([str(t) for t in allowed_types])
    )


def verify_function_return_type(func: Callable):
    return_type = get_function_return_class(func)

    # None is not allowed as return type
    if return_type is None:
        raise TypeError(
            f"{func.__name__} returns None; RPC functions must return a value"
        )

    # Optional is not allowed as return type
    if get_origin(return_type) == typing.Union and type(None) in return_type.__args__:
        raise TypeError(
            f"{func.__name__} returns Optional; RPC functions must return a value"
        )

    if is_allowed_type(return_type):
        return

    raise TypeError(
        f"{func.__name__} has return type {return_type} which is not allowed; "
        "allowed types are: \n" + "\n".join([str(t) for t in allowed_types])
    )


def verify_allowed_type(msg, rpc_method: Optional[str] = None):
    if not isinstance(msg, tuple(allowed_types)):
        method_name = f"for method `{rpc_method}`" if rpc_method else ""
        raise TypeError(
            f"{msg} is not allowed {method_name}; allowed types are: \n"
            + "\n".join([str(t) for t in allowed_types])
        )


def is_allowed_type(typ: Type):
    if typ in allowed_types:
        return True

    if str(typ).startswith("<enum"):
        return True

    if dataclasses.is_dataclass(typ):
        return True

    origin_type = get_origin(typ)
    if origin_type is not None and origin_type in allowed_types:
        return True

    for mtype in msgspec_types:
        if issubclass(typ, mtype):
            return True

    if _is_pydantic_model_type(typ):
        return True

    return False


def _is_pydantic_model_type(typ: Type) -> bool:
    return any(
        base.__module__.startswith("pydantic") and base.__name__ == "BaseModel"
        for base in typ.__mro__
    )
