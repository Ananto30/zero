from typing import Tuple

import zmq
import zmq.asyncio

from zero.utils import util


def zpipe_async(
    ctx: zmq.asyncio.Context,
) -> Tuple[zmq.asyncio.Socket, zmq.asyncio.Socket]:  # pragma: no cover
    """
    Build inproc pipe for talking to threads

    mimic pipe used in czmq zthread_fork.

    Returns a pair of PAIRs connected via inproc
    """
    sock_a = ctx.socket(zmq.PAIR)
    sock_b = ctx.socket(zmq.PAIR)
    sock_a.linger = sock_b.linger = 0
    sock_a.hwm = sock_b.hwm = 1
    sock_a.sndtimeo = sock_b.sndtimeo = 0
    sock_a.rcvtimeo = sock_b.rcvtimeo = 0
    iface = f"inproc://{util.unique_id()}"
    sock_a.bind(iface)
    sock_b.connect(iface)
    return sock_a, sock_b
