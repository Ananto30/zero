import pytest

from tests import constants
from tests.utils import kill_process, start_server

from .server1 import run as server1_run
from .server2 import run as server2_run

try:
    from pytest_cov.embed import cleanup_on_sigterm
except ImportError:
    pass
else:
    cleanup_on_sigterm()


@pytest.fixture(scope="session")
def server1():
    process = start_server(constants.MULTIPLE_SERVERS_PORT1, server1_run)
    yield process
    kill_process(process)


@pytest.fixture(scope="session")
def server2():
    process = start_server(constants.MULTIPLE_SERVERS_PORT2, server2_run)
    yield process
    kill_process(process)
