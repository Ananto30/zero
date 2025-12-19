#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
High-performance ZeroMQ PubSub Broker using a synchronous reactor loop.

Key design:
1. **Synchronous zmq.Poller**: C-level polling without asyncio overhead.
2. **Combined event loop**: Handle PULL, ROUTER, periodic flush, and watchdog in one loop.
3. **Heartbeat Tracking**: Crash if no activity within a timeout.
4. **Atomic persistence**: Flush offsets to disk with tmp replace.
5. **LINGER=0 & HWM tuning**: Fast shutdown and high throughput.
"""
import argparse
import json
import logging
import signal
import sys
import time
from pathlib import Path

import zmq

from zero.pubsub.segment_manager import SegmentManager

# ─────────────────────────────────────────────────────────────────────────────
# Arg parsing
# ─────────────────────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser(
    description="Synchronous Reactor ZeroMQ Broker"
)
parser.add_argument("--host", default="*", help="Interface to bind")
parser.add_argument("--pull-port", type=int, default=5555)
parser.add_argument("--pub-port", type=int, default=5556)
parser.add_argument("--router-port", type=int, default=5557)
parser.add_argument("--ack-port", type=int, default=5558)
parser.add_argument("--log-dir", default="logs")
parser.add_argument("--offset-db", default="offset_tracker.json")
parser.add_argument("--persist-interval", type=float, default=5.0)
parser.add_argument("--heartbeat-timeout", type=float, default=10.0,
    help="Seconds of inactivity before watchdog kills broker")
parser.add_argument("--poll-timeout", type=int, default=1000,
    help="Poller timeout in milliseconds")
parser.add_argument("--log-level", default="INFO")
args = parser.parse_args()

# ─────────────────────────────────────────────────────────────────────────────
# Logging setup
# ─────────────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=getattr(logging, args.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)-8s %(message)s",
)
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Broker
# ─────────────────────────────────────────────────────────────────────────────
class Broker:
    def __init__(self, args):
        # ZMQ context and sockets
        self.ctx = zmq.Context.instance()
        self.pull = self.ctx.socket(zmq.PULL)
        self.pull.bind(f"tcp://{args.host}:{args.pull_port}")
        self.pub = self.ctx.socket(zmq.PUB)
        self.pub.bind(f"tcp://{args.host}:{args.pub_port}")
        self.router = self.ctx.socket(zmq.ROUTER)
        self.router.bind(f"tcp://{args.host}:{args.router_port}")
        self.ack_pub = self.ctx.socket(zmq.PUB)
        self.ack_pub.bind(f"tcp://{args.host}:{args.ack_port}")

        # Fast shutdown: drop unsent messages
        for sock in (self.pull, self.pub, self.router, self.ack_pub):
            sock.setsockopt(zmq.LINGER, 0)
            sock.setsockopt(zmq.SNDHWM, 10000)
            sock.setsockopt(zmq.RCVHWM, 10000)

        # Poller for multiplexing
        self.poller = zmq.Poller()
        self.poller.register(self.pull, zmq.POLLIN)
        self.poller.register(self.router, zmq.POLLIN)

        # Log manager and offsets
        self.mgr = SegmentManager(args.log_dir)
        self.offsets_path = Path(args.offset_db)
        self.offsets = self._load_offsets()
        self._dirty = False

        # Timing
        self.persist_interval = args.persist_interval
        self.heartbeat_timeout = args.heartbeat_timeout
        self.poll_timeout = args.poll_timeout

        self._last_beat = time.time()
        self._shutdown = False
        
    def _load_offsets(self):
        if self.offsets_path.exists():
            try:
                data = json.loads(self.offsets_path.read_text())
                logger.info("Loaded offsets from %s", self.offsets_path)
                return data
            except Exception:
                logger.exception("Offsets load failed, starting fresh")
        return {}

    def _persist_offsets(self):
        tmp = self.offsets_path.with_suffix('.tmp')
        tmp.write_text(json.dumps(self.offsets))
        tmp.replace(self.offsets_path)
        logger.debug("Offsets persisted")
        self._dirty = False

    def _beat(self):
        self._last_beat = time.time()

    def _shutdown_signal(self, signum, frame):
        logger.info("Signal %d received, shutting down", signum)
        self._shutdown = True

    def run(self):
        # Register shutdown signals
        signal.signal(signal.SIGINT, self._shutdown_signal)
        signal.signal(signal.SIGTERM, self._shutdown_signal)

        logger.info("Broker starting: PULL@%d, PUB@%d, ROUTER@%d, ACK@%d",
                    args.pull_port, args.pub_port, args.router_port, args.ack_port)
        next_persist = time.time() + self.persist_interval

        try:
            while not self._shutdown:
                # Poll for incoming events
                events = dict(self.poller.poll(self.poll_timeout))

                if self.pull in events:
                    client_b, topic_b, msgid_b, msg = self.pull.recv_multipart()
                    ts = int(time.time() * 1000)
                    topic = topic_b.decode()

                    # 1) Append to log (fast C-coded append)
                    self.mgr.append(topic, msg, ts)
                    # 2) Publish live
                    offset = self.mgr.next_offset(topic) - 1
                    self.pub.send_multipart([topic_b, str(offset).encode(), str(ts).encode(), msg])
                    # 3) Ack
                    ack_topic = b"acks." + client_b
                    self.ack_pub.send_multipart([ack_topic, msgid_b])

                    self._beat()

                if self.router in events:
                    frames = self.router.recv_multipart()
                    client_id = frames[0]
                    body = frames[-1]
                    try:
                        req = json.loads(body.decode())
                    except Exception:
                        logger.exception("Invalid JSON: %r", body)
                        self._beat()
                        continue

                    c, t, kind = req.get("client_id"), req.get("topic"), req.get("type")
                    if not (c and t and kind):
                        logger.warning("Malformed request %r", req)
                        self._beat()
                        continue

                    self.offsets.setdefault(c, {}).setdefault(t, 0)
                    if kind == "replay":
                        mode = req.get("mode", "tracked")
                        if mode == "latest":
                            start = self.mgr.next_offset(t) - 1
                        elif mode == "tracked":
                            start = self.offsets[c][t]
                        elif mode == "timestamp":
                            start = self.mgr.find_offset_from_timestamp(t, req.get("timestamp", 0))
                        else:
                            start = 0
                        for off, ts, payload in self.mgr.read_from_offset(t, start):
                            self.router.send_multipart([client_id, t.encode(), str(off).encode(), str(ts).encode(), payload])
                    elif kind == "ack":
                        off = req.get("offset")
                        if off is not None:
                            self.offsets[c][t] = off
                            self._dirty = True
                        self.router.send_multipart([client_id, b"{\"status\":\"ok\"}"])
                    else:
                        logger.warning("Unknown type %r", kind)

                    self._beat()

                now = time.time()
                # Periodic persistence
                if now >= next_persist:
                    if self._dirty:
                        self._persist_offsets()
                    next_persist = now + self.persist_interval
                # Watchdog check
                if now - self._last_beat > self.heartbeat_timeout:
                    raise RuntimeError(f"No activity for {now - self._last_beat:.1f}s, exiting")

            # Final cleanup
            if self._dirty:
                self._persist_offsets()
            logger.info("Broker cleanly shut down")
        except Exception:
            logger.exception("Broker crashed")
            sys.exit(1)

# ─────────────────────────────────────────────────────────────────────────────
# Entrypoint
# ─────────────────────────────────────────────────────────────────────────────

def main():
    broker = Broker(args)
    broker.run()

if __name__ == "__main__":
    main()
