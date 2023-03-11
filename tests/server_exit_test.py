import sys
import subprocess
import pathlib
import pytest


def test_simple_server_exit():        
    p:subprocess.CompletedProcess=subprocess.run([sys.executable, "server_exit.py"], capture_output=True, cwd=pathlib.Path(__file__).parent.resolve(), timeout=11)
    stdout=p.stdout.decode()  if p.stdout is not None else "" 
    stderr=p.stderr.decode()  if p.stderr is not None else ""

    # to see output uncomment fillowing: 
    try:
        
        outlines=stdout.splitlines()
        assert not outlines[-1].endswith('self terminate after 10 sec') # it shouldn't terminate it should exitd

        errlines=stderr.splitlines()
        assert errlines[-2].endswith('Caught KeyboardInterrupt, terminating workers') # normal exiting output
        assert errlines[-1].endswith('server > Terminating server')                   # normal exiting output

        p.check_returncode()

    except Exception as e:
        print("stdout"); print(stdout); print("stderr  "); print(stderr)
        raise e
