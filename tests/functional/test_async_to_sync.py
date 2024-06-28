import asyncio

import pytest

from zero.utils.async_to_sync import async_to_sync


# Test case 1: Test a simple async function
async def simple_async_function(x):
    await asyncio.sleep(0.1)  # Simulate async work
    return x * 2


def test_simple_async_function():
    sync_function = async_to_sync(simple_async_function)
    result = sync_function(5)
    assert result == 10, "The async function should return 10 when called with 5"


# Test case 2: Test an async function that raises an exception
async def async_function_raises_exception():
    raise ValueError("This is a test exception")


def test_async_function_exception():
    sync_function = async_to_sync(async_function_raises_exception)
    with pytest.raises(ValueError) as exc_info:
        sync_function()
    assert (
        str(exc_info.value) == "This is a test exception"
    ), "The exception message should be 'This is a test exception'"


# Test case 3: Test the reusability of async_to_sync for multiple functions
async def another_simple_async_function(x):
    await asyncio.sleep(0.1)  # Simulate async work
    return x + 100


def test_reusability_of_async_to_sync():
    sync_function_1 = async_to_sync(simple_async_function)
    result_1 = sync_function_1(5)
    assert (
        result_1 == 10
    ), "The first async function should return 10 when called with 5"

    sync_function_2 = async_to_sync(another_simple_async_function)
    result_2 = sync_function_2(5)
    assert (
        result_2 == 105
    ), "The second async function should return 105 when called with 5"
