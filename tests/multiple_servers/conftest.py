from multiprocessing import Process

import pytest

from tests.multiple_servers.config import Config
from tests.multiple_servers.server1 import run as server1_run
from tests.multiple_servers.server2 import run as server2_run
from tests.utils import ping_until_success


@pytest.fixture(scope="session")
def server1():
    p = Process(target=server1_run, args=(Config.SERVER1_PORT,))
    p.start()
    ping_until_success(Config.SERVER1_PORT)
    yield p
    p.terminate()


@pytest.fixture(scope="session")
def server2():
    p = Process(target=server2_run, args=(Config.SERVER2_PORT,))
    p.start()
    ping_until_success(Config.SERVER2_PORT)
    yield p
    p.terminate()
