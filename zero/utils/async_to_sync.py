import asyncio
import threading
from functools import wraps

_LOOP = None
_THRD = None


def start_async_loop():
    global _LOOP, _THRD  # pylint: disable=global-statement
    if _LOOP is None or _THRD is None or not _THRD.is_alive():
        _LOOP = asyncio.new_event_loop()
        _THRD = threading.Thread(target=_LOOP.run_forever, name="Async Runner", daemon=True)
        _THRD.start()


def async_to_sync(func):
    @wraps(func)
    def run(*args, **kwargs):
        start_async_loop()  # Ensure the loop and thread are started
        try:
            future = asyncio.run_coroutine_threadsafe(func(*args, **kwargs), _LOOP)
            return future.result()
        except Exception as exc:
            print(f"Exception occurred: {exc}")
            raise

    return run
