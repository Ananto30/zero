import pytest

from zero import AsyncZeroClient

async_client = AsyncZeroClient("localhost", 5559)


@pytest.mark.asyncio
async def test_concurrent_divide():
    req_resp = {
        (10, 2): 5,
        (10, 3): 3,
        (10, 4): 2,
        (10, 5): 2,
        (534, 2): 267,
        (534, 3): 178,
        (534, 4): 133,
        (534, 5): 106,
        (534, 6): 89,
        (534, 7): 76,
        (534, 8): 66,
        (534, 9): 59,
        (534, 10): 53,
        (534, 11): 48,
    }

    for req, resp in req_resp.items():
        assert await async_client.call("divide", req) == resp
