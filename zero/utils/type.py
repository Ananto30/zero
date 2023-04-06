from typing import (
    Callable,
    Dict,
    List,
    Optional,
    Tuple,
    Union,
    get_origin,
    get_type_hints,
)

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
    List,
    Tuple,
    Dict,
]
special_types = [
    Union,
    Optional,
]
pydantic_types = [
    # BaseModel,  TODO: next feature
]


allowed_types = basic_types + typing_types + special_types + pydantic_types


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
    return_count = func.__code__.co_argcount
    if return_count > 1:
        raise ValueError(
            f"`{func.__name__}` has more than 1 return values; "
            "RPC functions can have only one return value"
        )

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
    if input_type in basic_types:
        return
    if get_origin(input_type) in basic_types:
        return
    if get_origin(input_type) in special_types:
        return
    if issubclass(input_type, tuple(pydantic_types)):
        return

    raise TypeError(
        f"{func.__name__} has type {input_type} which is not allowed; "
        "allowed types are: \n" + "\n".join([str(t) for t in allowed_types])
    )


def verify_function_return_type(func: Callable):
    return_type = get_function_return_class(func)
    if return_type is None:
        return
    if return_type in basic_types:
        return
    if get_origin(return_type) in basic_types:
        return
    if get_origin(return_type) in special_types:
        return
    if issubclass(return_type, tuple(pydantic_types)):
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


def verify_incoming_rpc_call_input_type(
    msg, rpc_method: str, rpc_input_type_map: dict
):  # pragma: no cover
    input_type = rpc_input_type_map[rpc_method]
    if input_type is None:
        return

    if input_type in basic_types:
        if input_type != type(msg):
            raise TypeError(
                f"{msg} is not allowed for method `{rpc_method}`; allowed type: {input_type}"
            )

    origin_type = get_origin(input_type)
    if origin_type in basic_types:
        if origin_type != type(msg):
            raise TypeError(
                f"{msg} is not allowed for method `{rpc_method}`; allowed type: {input_type}"
            )


def is_pydantic(cls):  # pragma: no cover
    if cls not in basic_types:
        if not get_origin(cls) in basic_types:
            if not get_origin(cls) in special_types:
                if issubclass(cls, tuple(pydantic_types)):
                    return True
