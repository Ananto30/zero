import asyncio
import threading
from functools import wraps

_loop = None
_thrd = None


def start_async_loop():
    global _loop, _thrd
    if _loop is None or _thrd is None or not _thrd.is_alive():
        _loop = asyncio.new_event_loop()
        _thrd = threading.Thread(
            target=_loop.run_forever, name="Async Runner", daemon=True
        )
        _thrd.start()


def async_to_sync(func):
    @wraps(func)
    def run(*args, **kwargs):
        start_async_loop()  # Ensure the loop and thread are started
        try:
            future = asyncio.run_coroutine_threadsafe(func(*args, **kwargs), _loop)
            return future.result()
        except Exception as e:
            print(f"Exception occurred: {e}")
            raise

    return run
