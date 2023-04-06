from typing import Tuple

import zmq
import zmq.asyncio

from zero.utils.util import unique_id


def zpipe(
    ctx: zmq.Context, timeout: int = 1000
) -> Tuple[zmq.Socket, zmq.Socket]:  # pragma: no cover
    """
    Build inproc pipe for talking to threads

    mimic pipe used in czmq zthread_fork.

    Returns a pair of PAIRs connected via inproc
    """
    a = ctx.socket(zmq.PAIR)
    b = ctx.socket(zmq.PAIR)
    a.linger = b.linger = 0
    a.hwm = b.hwm = 1
    a.sndtimeo = b.sndtimeo = timeout
    a.rcvtimeo = b.rcvtimeo = timeout
    iface = f"inproc://{unique_id()}"
    a.bind(iface)
    b.connect(iface)
    return a, b


def zpipe_async(
    ctx: zmq.asyncio.Context, timeout: int = 1000
) -> Tuple[zmq.asyncio.Socket, zmq.asyncio.Socket]:
    """
    Build inproc pipe for talking to threads

    mimic pipe used in czmq zthread_fork.

    Returns a pair of PAIRs connected via inproc
    """
    a = ctx.socket(zmq.PAIR)
    b = ctx.socket(zmq.PAIR)
    a.linger = b.linger = 0
    a.hwm = b.hwm = 1
    a.sndtimeo = b.sndtimeo = timeout
    a.rcvtimeo = b.rcvtimeo = timeout
    iface = f"inproc://{unique_id()}"
    a.bind(iface)
    b.connect(iface)
    return a, b
