import pytest

from zero import ZeroServer
from zero.errors import ZeroException


def function_with_2_args_no_typing(a, b):
    return a + b


def function_with_2_args_with_typing(a: int, b: int) -> int:
    return a + b


def function_with_no_args_no_return_type():
    return "Hello World"


def function_with_no_args() -> str:
    return "Hello World"


def function_with_1_arg_no_typing(a):
    return a


def function_with_1_arg_with_typing(a: str) -> str:
    return a


def function_with_1_arg_no_return_type(a: str):
    return a


def test_function_with_no_args():
    app = ZeroServer()
    app.register_rpc(function_with_no_args)


def test_function_with_no_args_no_return_type():
    app = ZeroServer()
    with pytest.raises(ZeroException) as e:
        app.register_rpc(function_with_no_args_no_return_type)
    assert (
        str(e.value)
        == "`function_with_no_args_no_return_type` has no return type hinting; RPC functions must have type hints"
    )


def test_function_with_2_args_no_typing():
    app = ZeroServer()
    with pytest.raises(ZeroException) as e:
        app.register_rpc(function_with_2_args_no_typing)
    assert (
        str(e.value)
        == "`function_with_2_args_no_typing` has more than 1 args; RPC functions can have only one arg - msg, or no arg"
    )


def test_function_with_2_args_with_typing():
    app = ZeroServer()
    with pytest.raises(ZeroException) as e:
        app.register_rpc(function_with_2_args_with_typing)
    assert (
        str(e.value)
        == "`function_with_2_args_with_typing` has more than 1 args; RPC functions can have only one arg - msg, or no arg"
    )


def test_function_with_1_arg_no_typing():
    app = ZeroServer()
    with pytest.raises(ZeroException) as e:
        app.register_rpc(function_with_1_arg_no_typing)
    assert (
        str(e.value)
        == "`function_with_1_arg_no_typing` has no type hinting; RPC functions must have type hints"
    )


def test_function_with_1_arg_with_typing():
    app = ZeroServer()
    app.register_rpc(function_with_1_arg_with_typing)


def test_function_with_1_arg_no_return_type():
    app = ZeroServer()
    with pytest.raises(ZeroException) as e:
        app.register_rpc(function_with_1_arg_no_return_type)
    assert (
        str(e.value)
        == "`function_with_1_arg_no_return_type` has no return type hinting; RPC functions must have type hints"
    )
