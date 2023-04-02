import pytest

from tests.utils import kill_subprocess, start_subprocess

from . import server

try:
    from pytest_cov.embed import cleanup_on_sigterm
except ImportError:
    pass
else:
    cleanup_on_sigterm()


@pytest.fixture(autouse=True, scope="session")
def base_server():
    process = start_subprocess("tests.functional.single_server.server")
    yield
    kill_subprocess(process)
