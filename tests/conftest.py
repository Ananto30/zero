import asyncio
import sys

import pytest


# Ensure the test process uses the selector event loop on Windows.
# This avoids the Proactor->selector fallback used by pyzmq and keeps
# behavior consistent with server subprocesses which also set this policy.
@pytest.fixture(scope="session", autouse=True)
def _use_selector_event_loop_policy_on_windows():
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
