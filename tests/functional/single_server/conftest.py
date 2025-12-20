import multiprocessing
import sys

import pytest

from tests.utils import kill_subprocess, start_subprocess

# Set spawn method for multiprocessing to avoid fork() warnings with asyncio
multiprocessing.set_start_method("spawn", force=True)

try:
    from pytest_cov.embed import cleanup_on_sigterm
except ImportError:
    pass
else:
    cleanup_on_sigterm()


@pytest.fixture(autouse=True, scope="session")
def base_server():
    process = start_subprocess("tests.functional.single_server.server", 5559)
    yield
    kill_subprocess(process)


@pytest.fixture(autouse=True, scope="session")
def threaded_server():
    process = start_subprocess("tests.functional.single_server.threaded_server", 7777)
    yield
    kill_subprocess(process)


if sys.platform != "win32":

    @pytest.fixture(autouse=True, scope="session")
    def tcp_server():
        process = start_subprocess("tests.functional.single_server.tcp_server", 5560)
        yield
        kill_subprocess(process)
