import pytest

from tests.single_server import server
from tests.utils import kill_process, start_server

try:
    from pytest_cov.embed import cleanup_on_sigterm
except ImportError:
    pass
else:
    cleanup_on_sigterm()


@pytest.fixture(autouse=True, scope="session")
def base_server():
    process = start_server(server.PORT, server.run)
    yield
    kill_process(process)
