import threading
import time
from datetime import datetime
from queue import Empty, Queue
from typing import Callable, Optional

import zmq


class Message:
    """
    Represents a single message received from the broker.

    Attributes:
      topic     - the topic string this message belongs to
      offset    - broker-assigned monotonic offset for the topic
      timestamp - milliseconds since epoch when the broker logged it
      payload   - raw message bytes
    """

    __slots__ = ("topic", "offset", "timestamp", "payload")

    def __init__(self, topic: str, offset: int, timestamp: int, payload: bytes):
        self.topic = topic
        self.offset = offset
        self.timestamp = timestamp
        self.payload = payload

    def __repr__(self):
        # Show ISO‑formatted timestamp for readability
        ts = datetime.fromtimestamp(self.timestamp / 1000).isoformat()
        return f"<Message topic={self.topic!r} offset={self.offset} ts={ts!r}>"


class ZeroSubscriber:
    """
    ZeroMQ-based consumer with batched acknowledgments.

    Usage:
      c = Consumer(broker_host, topic, ack_batch_size=100, ack_interval_ms=2000)
      c.register_func(my_handler, replay_mode="tracked")

      # register_func is blocking: it will perform replay, then listen for live messages.
      # if you want to run it in the background, use threading:

      thread = threading.Thread(target=c.register_func, args=(my_handler,))
      thread.start()

    Design & Behavior:
      • On register_func:
        1) Sets up DEALER socket for replay & ACK
        2) Sets up SUB socket for live stream
        3) Starts a background thread to batch & send ACKs
        4) Sends a replay request and enters the blocking receive loop
      • Incoming messages (replay or live) are wrapped in Message,
        delivered to user callback, then queued for ACK.
      • ACKs are sent in batches or on a timer to reduce RPC overhead.
    """

    def __init__(
        self,
        broker_host: str,
        topic: str,
        client_id: str,
        pub_port: int = 5556,
        router_port: int = 5557,
        ack_batch_size: int = 100,
        ack_interval_ms: int = 1000,
    ):
        """
        Parameters
        ----------
        broker_host: str
            Hostname or IP of the ZeroMQ broker.
        topic: str
            Topic to subscribe to.
        client_id: str
            Unique client ID for this consumer, used for replay and ACKs.
        pub_port: int
            Port of the broker's publisher socket.
        router_port: int
            Port of the broker's router socket.
        ack_batch_size: int
            Number of ACKs to batch before sending.
        ack_interval_ms: int
            Interval in milliseconds to flush ACKs even if batch size is not reached.
            This helps ensure timely delivery of ACKs even under low message rates.
        """
        # Broker connection info
        self.pub_addr = f"tcp://{broker_host}:{pub_port}"
        self.router_addr = f"tcp://{broker_host}:{router_port}"
        self.topic = topic
        # Unique client ID for replay & ACKs
        self.client_id = client_id
        # ACK batching parameters
        self.ack_batch_size = ack_batch_size
        self.ack_interval_ms = ack_interval_ms

        # Will be set in register_func()
        self._callback: Callable[[Message], None] = None  # type: ignore
        self._replay_mode: str = None  # type: ignore # "latest" | "tracked" | "timestamp"
        self._ts_to_seek: Optional[int] = None  # ms since epoch if timestamp mode

        # ZMQ sockets and poller
        self._ctx: zmq.Context = None  # type: ignore
        self._dealer: zmq.Socket = None  # type: ignore
        self._sub: zmq.Socket = None  # type: ignore
        self._poller: zmq.Poller = None  # type: ignore

        # Queue for ACKs: holds (topic, offset)
        self._ack_queue: Queue[tuple[str, int]] = Queue()
        self._stop_ack_thread = threading.Event()

    def register_func(
        self,
        func: Callable[[Message], None],
        replay_mode: str = "tracked",
        timestamp: Optional[int] = None,
    ):
        """
        Register the user callback and start consuming.

        func         - function to call for each Message
        replay_mode  - "latest", "tracked", or "timestamp"
        timestamp    - when replay_mode=="timestamp", an int ms-since-epoch

        This method blocks:
          • Sends the replay request
          • Runs the receive loop for replay & live messages
        """
        # Store user parameters
        self._callback = func
        self._replay_mode = replay_mode
        self._ts_to_seek = timestamp

        # Initialize ZMQ sockets & poller
        self._setup_zmq()

        # Start ACK flusher in background to batch ACKs
        self._start_ack_flusher()

        # Blocking receive loop: handles replay replies then live messages
        self._run()

    def _start_ack_flusher(self):
        """
        Helper to (re)start the ACK flusher thread.
        This is useful if the flusher dies unexpectedly.
        """
        self._stop_ack_thread.clear()
        self._ack_thread = threading.Thread(target=self._ack_flusher, name="AckFlusher")
        self._ack_thread.daemon = True
        self._ack_thread.start()

    def _setup_zmq(self):
        """Create and connect DEALER (replay/ACK) and SUB (live) sockets."""
        self._ctx = zmq.Context.instance()

        # DEALER socket uses client_id as ZMQ identity
        self._dealer = self._ctx.socket(zmq.DEALER)
        self._dealer.setsockopt(zmq.IDENTITY, self.client_id.encode())
        self._dealer.connect(self.router_addr)

        # SUB socket subscribes only to the chosen topic
        self._sub = self._ctx.socket(zmq.SUB)
        self._sub.connect(self.pub_addr)
        self._sub.setsockopt_string(zmq.SUBSCRIBE, self.topic)

        # Poller watches both sockets for incoming messages
        self._poller = zmq.Poller()
        self._poller.register(self._dealer, zmq.POLLIN)
        self._poller.register(self._sub, zmq.POLLIN)

    def _run(self):
        """Blocking loop: request history replay, then process messages forever."""
        # Send replay request to broker
        req = {
            "type": "replay",
            "client_id": self.client_id,
            "topic": self.topic,
            "mode": self._replay_mode,
        }
        if self._replay_mode == "timestamp" and self._ts_to_seek is not None:
            req["timestamp"] = self._ts_to_seek
        self._dealer.send_json(req)

        # Process incoming frames from broker
        while True:
            socks = dict(self._poller.poll())

            # Replay responses come on DEALER socket
            if self._dealer in socks:
                frames = self._dealer.recv_multipart()
                # Single‑frame messages are ACK replies => ignore
                if len(frames) == 1:
                    continue
                # Expected 4‑frame: [topic, offset, ts, payload]
                topic_b, off_b, ts_b, payload = frames
                msg = Message(
                    topic_b.decode(), int(off_b.decode()), int(ts_b.decode()), payload
                )
                self._process_and_queue_ack(msg)

            # Live messages come on SUB socket
            if self._sub in socks:
                topic_b, off_b, ts_b, payload = self._sub.recv_multipart()
                msg = Message(
                    topic_b.decode(), int(off_b.decode()), int(ts_b.decode()), payload
                )
                self._process_and_queue_ack(msg)

            # Supervise the flusher: if it somehow died, restart it
            if not self._ack_thread.is_alive():
                print("[ConsumerLoop] ACK flusher died—restarting…")
                self._start_ack_flusher()  # a small helper to (re)spawn it

    def _process_and_queue_ack(self, msg: Message):
        """
        Invoke the user's callback, then enqueue an ACK for this message.

        Splits responsibility:
          1) Callback may block or raise; swallow exceptions to keep flow alive.
          2) ACK queue is fed for the flusher thread to batch.
        """
        try:
            self._callback(msg)
        except Exception:
            pass

        # Always queue the (topic, offset); flusher will pick highest offset
        self._ack_queue.put((msg.topic, msg.offset))

    def _ack_flusher(self):
        """
        Background thread that batches acknowledgments.

        Collects up to ack_batch_size or waits ack_interval_ms, then sends
        one JSON ACK per topic with the maximum offset seen.
        """
        last_flush = time.time()
        pending = {}  # topic -> highest offset

        while not self._stop_ack_thread.is_set():
            now = time.time()
            timeout = max(0, (self.ack_interval_ms / 1000) - (now - last_flush))

            # Wait for next ACK or timeout
            try:
                topic, offset = self._ack_queue.get(timeout=timeout)
                pending[topic] = max(offset, pending.get(topic, -1))
            except Empty:
                pass

            # Flush if batch full or timer expired
            if (
                len(pending) >= self.ack_batch_size
                or (time.time() - last_flush) * 1000 >= self.ack_interval_ms
            ):
                if pending:
                    for topic, offset in pending.items():
                        ack = {
                            "type": "ack",
                            "client_id": self.client_id,
                            "topic": topic,
                            "offset": offset,
                        }
                        # Fire-and-forget ACK
                        self._dealer.send_json(ack)
                    pending.clear()
                last_flush = time.time()

    def close(self):
        """
        Stop the ACK flusher and close ZMQ sockets.

        Blocks briefly to allow a final flush of ACKs.
        """
        self._stop_ack_thread.set()
        # Wait to flush any remaining ACKs
        time.sleep(self.ack_interval_ms / 1000 + 0.1)
        self._dealer.close(0)
        self._sub.close(0)
        self._ctx.term()
