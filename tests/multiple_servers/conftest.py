import pytest

from tests.multiple_servers.config import Config
from tests.multiple_servers.server1 import run as server1_run
from tests.multiple_servers.server2 import run as server2_run
from tests.utils import kill_process, start_server

try:
    from pytest_cov.embed import cleanup_on_sigterm
except ImportError:
    pass
else:
    cleanup_on_sigterm()


@pytest.fixture(scope="session")
def server1():
    process = start_server(Config.SERVER1_PORT, server1_run)
    yield process
    kill_process(process)


@pytest.fixture(scope="session")
def server2():
    process = start_server(Config.SERVER2_PORT, server2_run)
    yield process
    kill_process(process)
