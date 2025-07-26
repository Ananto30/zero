import subprocess  # nosec
from multiprocessing import Process

from tests.utils import kill_process, kill_subprocess, process_map


def pytest_sessionfinish(session, exitstatus):
    print("\n")
    print("[PYTEST] Session is finishing, exitstatus:", exitstatus)

    if process_map.values():
        print(
            f"[PYTEST] There are {len(process_map)} processes still running at the end of the session:"
        )
    for process in process_map.values():
        print(f" - {process}")
        if isinstance(process, subprocess.Popen):
            kill_subprocess(process)
            print(f"  alive: {process.poll() is None}")
        elif isinstance(process, Process):
            kill_process(process)
            print(f"  alive: {process.is_alive()}")
