import typing
from zero.errors import ZeroException


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

allowed_types = basic_types + typing_types + special_types


def verify_function_args(func: typing.Callable):
    arg_count = func.__code__.co_argcount
    if arg_count > 1:
        raise ZeroException(
            f"`{func.__name__}` has more than 1 args; RPC functions can have only one arg - msg, or no arg"
        )

    if arg_count == 1:
        arg_name = func.__code__.co_varnames[0]
        func_arg_type = typing.get_type_hints(func)
        if arg_name not in func_arg_type:
            raise ZeroException(f"`{func.__name__}` has no type hinting; RPC functions must have type hints")


def verify_function_return(func: typing.Callable):
    types = typing.get_type_hints(func)
    if not types.get("return"):
        raise ZeroException(f"`{func.__name__}` has no return type hinting; RPC functions must have type hints")


def get_function_input_class(func: typing.Callable):
    arg_count = func.__code__.co_argcount
    if arg_count == 0:
        return None
    if arg_count == 1:
        arg_name = func.__code__.co_varnames[0]
        func_arg_type = typing.get_type_hints(func)
        return func_arg_type[arg_name]


def get_function_return_class(func: typing.Callable):
    types = typing.get_type_hints(func)
    return types.get("return")


def verify_function_input_type(func: typing.Callable):
    if get_function_input_class(func) is None:
        return

    if (input_type := get_function_input_class(func)) not in basic_types:
        if not typing.get_origin(input_type) in basic_types:
            if not typing.get_origin(input_type) in special_types:
                raise TypeError(
                    f"{func.__name__} has type {input_type} which is not allowed; "
                    "allowed types are: \n" + "\n".join([str(t) for t in allowed_types])
                )
