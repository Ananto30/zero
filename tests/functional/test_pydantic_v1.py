import sys
import importlib
from typing import Iterator
import pytest


@pytest.fixture
def patch_pydantic_to_v1(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    import pydantic.v1

    # Patch sys.modules so any `import pydantic` gives you `pydantic.v1`
    monkeypatch.setitem(sys.modules, "pydantic", pydantic.v1)
    importlib.invalidate_caches()

    yield

    # Clean up after test
    importlib.invalidate_caches()


def test_module_with_pydantic_v1(patch_pydantic_to_v1: None) -> None:
    # Re-import your module so it sees `pydantic` as v1
    from zero.encoder import generic

    importlib.reload(generic)

    # Now run assertions that rely on v1 behavior
    assert not generic.IS_PYDANTIC_V2
