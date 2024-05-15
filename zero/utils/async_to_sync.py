import asyncio
import threading
from functools import wraps

_loop = asyncio.new_event_loop()

_thrd = threading.Thread(target=_loop.run_forever, name="Async Runner", daemon=True)


def async_to_sync(func):
    @wraps(func)
    def run(*args, **kwargs):
        if not _thrd.is_alive():
            _thrd.start()

        future = asyncio.run_coroutine_threadsafe(func(*args, **kwargs), _loop)
        return future.result()

    return run
