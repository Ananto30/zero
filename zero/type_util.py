import typing
import inspect
from zero.errors import ZeroException

# from pydantic import BaseModel

basic_types = [
    int,
    float,
    str,
    bool,
    list,
    dict,
    tuple,
    set,
]
typing_types = [
    typing.List,
    typing.Tuple,
    typing.Dict,
]
special_types = [
    typing.Union,
    typing.Optional,
]
pydantic_types = [
    # BaseModel,  TODO: next feature
]


allowed_types = basic_types + typing_types + special_types + pydantic_types


def verify_function_args(func: typing.Callable):
    arg_count = func.__code__.co_argcount

    if inspect.ismethod(func):
        max_argcount = 2
    else:
        max_argcount = 1

    if arg_count > max_argcount:
        raise ZeroException(
            f"`{func.__name__}` has more than 1 args; "
            "RPC functions can have only one arg - msg, or no arg"
        )

    if arg_count == max_argcount:
        arg_name = func.__code__.co_varnames[max_argcount - 1]
        func_arg_type = typing.get_type_hints(func)
        if arg_name not in func_arg_type:
            raise ZeroException(
                f"`{func.__name__}` has no type hinting; "
                "RPC functions must have type hints"
            )


def verify_function_return(func: typing.Callable):
    types = typing.get_type_hints(func)
    if not types.get("return"):
        raise ZeroException(
            f"`{func.__name__}` has no return type hinting; "
            "RPC functions must have type hints"
        )


def get_function_input_class(func: typing.Callable):
    arg_count = func.__code__.co_argcount
    if inspect.ismethod(func):
        max_argcount = 2
    else:
        max_argcount = 1
    if arg_count == max_argcount - 1:
        return None
    if arg_count == max_argcount:
        arg_name = func.__code__.co_varnames[max_argcount - 1]
        func_arg_type = typing.get_type_hints(func)
        return func_arg_type[arg_name]


def get_function_return_class(func: typing.Callable):
    types = typing.get_type_hints(func)
    return types.get("return")


def verify_function_input_type(func: typing.Callable):
    input_type = get_function_input_class(func)
    if input_type is None:
        return
    if input_type in basic_types:
        return
    if typing.get_origin(input_type) in basic_types:
        return
    if typing.get_origin(input_type) in special_types:
        return
    if issubclass(input_type, tuple(pydantic_types)):
        return

    raise TypeError(
        f"{func.__name__} has type {input_type} which is not allowed; "
        "allowed types are: \n" + "\n".join([str(t) for t in allowed_types])
    )


def verify_allowed_type(msg, rpc_method: str = None):
    if not isinstance(msg, tuple(allowed_types)):
        method_name = f"for method `{rpc_method}`" if rpc_method else ""
        raise TypeError(
            f"{msg} is not allowed {method_name}; allowed types are: \n" + "\n".join([str(t) for t in allowed_types])
        )


def verify_incoming_rpc_call_input_type(msg, rpc_method: str, rpc_input_type_map: dict):  # pragma: no cover
    it = rpc_input_type_map[rpc_method]
    if it is None:
        return

    if it in basic_types:
        if it != type(msg):
            raise TypeError(f"{msg} is not allowed for method `{rpc_method}`; allowed type: {it}")

    origin_type = typing.get_origin(it)
    if origin_type in basic_types:
        if origin_type != type(msg):
            raise TypeError(f"{msg} is not allowed for method `{rpc_method}`; allowed type: {it}")


def is_pydantic(cls):  # pragma: no cover
    if cls not in basic_types:
        if not typing.get_origin(cls) in basic_types:
            if not typing.get_origin(cls) in special_types:
                if issubclass(cls, tuple(pydantic_types)):
                    return True
