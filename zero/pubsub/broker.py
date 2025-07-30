#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import argparse
import json
import logging
import signal
import threading
import time
from pathlib import Path

import zmq

from zero.pubsub.segment_manager import SegmentManager

# ─────────────────────────────────────────────────────────────────────────────
#  Command‑line arguments
# ─────────────────────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser(
    description="ZeroMQ PubSub Broker with append-only log and at-least-once delivery"
)
parser.add_argument(
    "--host",
    default="*",
    help="Interface to bind (default: all)",
)
parser.add_argument(
    "--pull-port",
    type=int,
    default=5555,
    help="Port for PULL socket",
)
parser.add_argument(
    "--pub-port",
    type=int,
    default=5556,
    help="Port for PUB socket",
)
parser.add_argument(
    "--router-port",
    type=int,
    default=5557,
    help="Port for ROUTER socket",
)
parser.add_argument(
    "--ack-port",
    type=int,
    default=5558,
    help="Port for ACK PUB socket",
)
parser.add_argument(
    "--log-dir",
    default="logs",
    help="Base directory for topic logs",
)
parser.add_argument(
    "--offset-db",
    default="offset_tracker.json",
    help="File to persist consumer offsets",
)
parser.add_argument(
    "--persist-interval",
    type=float,
    default=5.0,
    help="Seconds between periodic offset DB flushes",
)
parser.add_argument("--log-level", default="INFO", help="Logging level")
args = parser.parse_args()

# ─────────────────────────────────────────────────────────────────────────────
#  Logging setup
# ─────────────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=getattr(logging, args.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)-8s %(threadName)s %(message)s",
)
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
#  ZMQ sockets & global state
# ─────────────────────────────────────────────────────────────────────────────
ctx = zmq.Context.instance()

pull_sock = ctx.socket(zmq.PULL)
pull_sock.bind(f"tcp://{args.host}:{args.pull_port}")

pub_sock = ctx.socket(zmq.PUB)
pub_sock.bind(f"tcp://{args.host}:{args.pub_port}")

router = ctx.socket(zmq.ROUTER)
router.bind(f"tcp://{args.host}:{args.router_port}")

ack_pub = ctx.socket(zmq.PUB)
ack_pub.bind(f"tcp://{args.host}:{args.ack_port}")  # e.g. args.ack_port=5558
ack_pub.setsockopt(zmq.LINGER, 0)

# linger=0 ensures fast shutdown: unsent msgs are dropped rather than blocking
for s in (pull_sock, pub_sock, router, ack_pub):
    s.setsockopt(zmq.LINGER, 0)

mgr = SegmentManager(args.log_dir)

offsets_lock = threading.Lock()
offsets_path = Path(args.offset_db)
# load existing offsets if present
if offsets_path.exists():
    try:
        offsets = json.loads(offsets_path.read_text())
        logger.info("Loaded offsets from %s", offsets_path)
    except Exception:
        logger.exception("Failed to load offsets, starting fresh")
        offsets = {}
else:
    offsets = {}

# track whether there are unsaved changes
_dirty = threading.Event()
_stop = threading.Event()


# ─────────────────────────────────────────────────────────────────────────────
#  Helper: persist offsets to disk
# ─────────────────────────────────────────────────────────────────────────────
def persist_offsets():
    """Write offsets to disk atomically."""
    try:
        tmp = offsets_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(offsets))
        tmp.replace(offsets_path)
        logger.debug("Persisted offsets to %s", offsets_path)
        _dirty.clear()
    except Exception:
        logger.exception("Error persisting offsets")


# ─────────────────────────────────────────────────────────────────────────────
#  Background thread: flush offsets periodically if dirty
# ─────────────────────────────────────────────────────────────────────────────
def offset_flusher():
    while not _stop.is_set():
        # wait up to persist_interval seconds, but wake early if dirty
        _dirty.wait(timeout=args.persist_interval)
        if _dirty.is_set():
            with offsets_lock:
                persist_offsets()


# ─────────────────────────────────────────────────────────────────────────────
#  Thread #1: ingest from publishers and log + live‑publish
# ─────────────────────────────────────────────────────────────────────────────
def publisher_loop():
    logger.info("Publisher loop started on %s:%d", args.host, args.pull_port)
    while not _stop.is_set():
        try:
            client_b, topic_b, msgid_b, msg = pull_sock.recv_multipart(
                flags=zmq.NOBLOCK
            )
        except zmq.Again:
            time.sleep(0.01)
            continue

        client_id = client_b.decode()
        topic = topic_b.decode()
        msg_id = msgid_b  # bytes
        ts = int(time.time() * 1000)

        # 1) append to segment log
        mgr.append(topic, msg, ts)

        # 2) publish live
        offset = mgr.next_offset(topic) - 1
        pub_sock.send_multipart([topic_b, str(offset).encode(), str(ts).encode(), msg])

        # 3) publish ack back to publisher
        #    topic = "acks.<client_id>"
        ack_topic = f"acks.{client_id}".encode()
        ack_pub.send_multipart([ack_topic, msg_id])


# ─────────────────────────────────────────────────────────────────────────────
#  Thread #2: handle replays & ACKs from consumers
# ─────────────────────────────────────────────────────────────────────────────
def router_loop():
    logger.info("Router loop started on %s:%d", args.host, args.router_port)
    while not _stop.is_set():
        try:
            frames = router.recv_multipart(flags=zmq.NOBLOCK)
        except zmq.Again:
            time.sleep(0.01)
            continue

        client_id = frames[0]
        # Strip optional empty delimiter
        if len(frames) == 3 and frames[1] == b"":
            body = frames[2]
        elif len(frames) == 2:
            body = frames[1]
        else:
            logger.warning("Unexpected frames=%d from %r", len(frames), client_id)
            continue

        try:
            req = json.loads(body.decode())
        except json.JSONDecodeError:
            logger.exception("Invalid JSON from %r: %r", client_id, body)
            continue

        c, t, kind = req.get("client_id"), req.get("topic"), req.get("type")
        if not all([c, t, kind]):
            logger.warning("Malformed request from %r: %s", client_id, req)
            continue

        with offsets_lock:
            offsets.setdefault(c, {}).setdefault(t, 0)

        if kind == "replay":
            mode = req.get("mode", "tracked")
            logger.info("Replay request: client=%s topic=%s mode=%s", c, t, mode)
            # Choose start offset
            if mode == "latest":
                start = mgr.next_offset(t) - 1
            elif mode == "tracked":
                start = offsets[c][t]
            elif mode == "timestamp":
                start = mgr.find_offset_from_timestamp(t, req.get("timestamp", 0))
            else:
                start = 0

            # Stream history
            for off, ts, payload in mgr.read_from_offset(t, start):
                try:
                    router.send_multipart(
                        [
                            client_id,
                            t.encode(),
                            str(off).encode(),
                            str(ts).encode(),
                            payload,
                        ]
                    )
                except Exception:
                    logger.exception("Failed to send replay to %r", c)

        elif kind == "ack":
            off = req.get("offset")
            if off is None:
                logger.warning("ACK missing offset from %r", c)
                continue
            logger.debug("ACK from %s topic=%s offset=%s", c, t, off)
            with offsets_lock:
                offsets[c][t] = off
                _dirty.set()

            # send minimal confirmation
            try:
                router.send_multipart(
                    [client_id, json.dumps({"status": "ok"}).encode()]
                )
            except Exception:
                logger.exception("Failed to reply ACK to %r", c)

        else:
            logger.warning("Unknown request type %r from %r", kind, c)


# ─────────────────────────────────────────────────────────────────────────────
#  Graceful shutdown on SIGINT / SIGTERM
# ─────────────────────────────────────────────────────────────────────────────
def on_signal(signum, frame):
    logger.info("Signal %d received, shutting down…", signum)
    _stop.set()


signal.signal(signal.SIGINT, on_signal)
signal.signal(signal.SIGTERM, on_signal)


# ─────────────────────────────────────────────────────────────────────────────
#  Main entrypoint
# ─────────────────────────────────────────────────────────────────────────────
def main():
    threads = []
    # start background flusher
    threads.append(
        threading.Thread(target=offset_flusher, name="OffsetFlusher", daemon=True)
    )

    threads.append(
        threading.Thread(target=publisher_loop, name="PublisherLoop", daemon=True)
    )
    threads.append(threading.Thread(target=router_loop, name="RouterLoop", daemon=True))

    for t in threads:
        t.start()

    logger.info(
        "Broker is up — PULL @%d, PUB @%d, ROUTER @%d",
        args.pull_port,
        args.pub_port,
        args.router_port,
    )

    # wait until a signal sets _stop
    while not _stop.is_set():
        time.sleep(1)

    # final flush
    with offsets_lock:
        persist_offsets()

    # tear down ZMQ
    pull_sock.close(0)
    pub_sock.close(0)
    router.close(0)
    ack_pub.close(0)
    ctx.term()
    logger.info("Broker cleanly shut down.")


if __name__ == "__main__":
    main()
