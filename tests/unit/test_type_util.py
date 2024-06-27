import unittest
from typing import Optional
from unittest.mock import MagicMock

from zero.utils.type_util import (
    get_function_input_class,
    get_function_return_class,
    verify_function_args,
    verify_function_input_type,
    verify_function_return,
    verify_function_return_type,
)


class TestVerifyFunctionReturnType(unittest.TestCase):
    def test_valid_return_type(self):
        def func() -> int:
            return 1

        verify_function_return_type(func)

    def test_none_return_type(self):
        def func() -> None:
            return None

        with self.assertRaises(TypeError):
            verify_function_return_type(func)

    def test_optional_return_type(self):
        def func() -> Optional[int]:
            return None

        with self.assertRaises(TypeError):
            verify_function_return_type(func)

    def test_invalid_return_type(self):
        class CustomType:
            pass

        def func() -> CustomType:
            return CustomType()

        with self.assertRaises(TypeError):
            verify_function_return_type(func)

    def test_mocked_return_type(self):
        def func() -> MagicMock:
            return MagicMock()

        with self.assertRaises(TypeError):
            verify_function_return_type(func)

    def test__verify_function_args__ok(self):
        def func(a: int) -> int:
            return a

        verify_function_args(func)

    def test__verify_function_args__multiple_args(self):
        def func(a: int, b: int) -> int:
            return a + b

        with self.assertRaises(ValueError):
            verify_function_args(func)

    def test__verify_function_args__no_type_hint(self):
        def func(a):
            return a

        with self.assertRaises(TypeError):
            verify_function_args(func)

    def test__verify_function_return__ok(self):
        def func() -> int:
            return 1

        verify_function_return(func)

    def test__verify_function_return__no_type_hint(self):
        def func():
            return 1

        with self.assertRaises(TypeError):
            verify_function_return(func)

    def test__get_function_input_class__ok(self):
        def func(a: int) -> int:
            return a

        self.assertEqual(get_function_input_class(func), int)

    def test__get_function_input_class__no_args(self):
        def func() -> int:
            return 1

        self.assertEqual(get_function_input_class(func), None)

    def test__get_function_input_class__multiple_args(self):
        def func(a: int, b: int) -> int:
            return a + b

        self.assertEqual(get_function_input_class(func), None)

    def test__get_function_return_class__ok(self):
        def func() -> int:
            return 1

        self.assertEqual(get_function_return_class(func), int)

    def test__get_function_return_class__no_return(self):
        def func():
            return 1

        self.assertEqual(get_function_return_class(func), None)

    def test__verify_function_input_type__ok(self):
        def func(a: int) -> int:
            return a

        verify_function_input_type(func)

    def test__verify_function_input_type__invalid(self):
        def func(a: MagicMock) -> int:
            return a

        with self.assertRaises(TypeError):
            verify_function_input_type(func)

    def test__verify_function_input_type__no_type_hint(self):
        def func(a) -> int:
            return a

        with self.assertRaises(KeyError):
            verify_function_input_type(func)
