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

    from pydantic import BaseModel

    class TestModel(BaseModel):
        name: str
        age: int

    encoder = generic.GenericEncoder()
    model_instance = TestModel(name="Alice", age=30)
    encoded_data = encoder.encode(model_instance)
    decoded_instance = encoder.decode_type(encoded_data, TestModel)
    assert decoded_instance.name == "Alice"
    assert decoded_instance.age == 30
