from typing import Tuple

import zmq

from zero.utils.util import unique_id


def zpipe(ctx: zmq.Context) -> Tuple[zmq.Socket, zmq.Socket]:
    """
    Build inproc pipe for talking to threads

    mimic pipe used in czmq zthread_fork.

    Returns a pair of PAIRs connected via inproc
    """
    a = ctx.socket(zmq.PAIR)
    b = ctx.socket(zmq.PAIR)
    a.linger = b.linger = 0
    a.hwm = b.hwm = 1
    iface = f"inproc://{unique_id()}"
    a.bind(iface)
    b.connect(iface)
    return a, b
