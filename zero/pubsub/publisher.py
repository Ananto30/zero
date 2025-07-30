import logging
import threading
import time
import uuid
from typing import Callable, Optional

import zmq

logger = logging.getLogger(__name__)


class CircuitOpenError(Exception):
    """Raised by publish() when the circuit is open (broker appears down)."""

    pass


class ConnectionTimeoutError(Exception):
    """Raised when we give up waiting for the initial broker connection."""


class ZeroPublisher:
    """
    Publisher for sending messages to a ZeroMQ broker.

    This publisher uses a PUSH socket to send messages and a SUB socket to
    receive acknowledgments (ACKs) from the broker. It supports back-pressure
    by limiting the number of unacknowledged messages in-flight, and it can
    handle circuit breaker logic to avoid overwhelming the broker if it becomes
    unavailable.

    If enable_broker_acks is True, it will wait for ACKs from the broker to ensure
    that messages are successfully received.
    Otherwise, it will send messages without waiting for ACKs. Which is much faster,
    but you may lose messages if the broker is down or unreachable.
    """

    def __init__(
        self,
        broker_host: str,
        *,
        push_port: int = 5555,
        ack_port: int = 5558,
        client_id: Optional[str] = None,
        ack_timeout: float = 1.0,
        max_unacked: int = 100,
        backpressure_timeout: float = 5.0,
        connect_timeout: float = 3.0,
        on_circuit_open: Optional[Callable[[], None]] = None,
        on_circuit_close: Optional[Callable[[], None]] = None,
        enable_broker_acks: bool = True,
    ):
        """
        Initialize the ZeroPublisher.

        Parameters
        ----------
        broker_host : str
            Hostname or IP address of the ZeroMQ broker.
        push_port : int
            Port for the PUSH socket to send messages to the broker.
        ack_port : int
            Port for the SUB socket to receive ACKs from the broker.
        client_id : Optional[str]
            Unique identifier for this publisher. If None, a random UUID will be used.
        ack_timeout : float
            Time in seconds to wait for an ACK before considering the message unacknowledged.
        max_unacked : int
            Maximum number of unacknowledged messages allowed in-flight. If exceeded, the circuit will
            open and no new messages will be sent until the circuit is closed.
        backpressure_timeout : float
            Time in seconds to wait before tripping the circuit if the in-flight window remains full.
        connect_timeout : float
            Time in seconds to wait for the initial connection to the broker before raising a timeout error.
        on_circuit_open : Optional[Callable[[], None]]
            Callback function to call when the circuit opens (broker appears down).
        on_circuit_close : Optional[Callable[[], None]]
            Callback function to call when the circuit closes (broker becomes available again).
        enable_broker_acks : bool
            Determines whether to wait for ACKs from the broker. If False, no circuit breaker logic is applied,
            and messages are sent without waiting for confirmation.
            This is faster but may result in lost messages if the broker is down.
        """
        self.client_id = client_id or uuid.uuid4().hex
        self.ack_timeout = ack_timeout
        self.max_unacked = max_unacked
        self.backpressure_timeout = backpressure_timeout
        self.connect_timeout = connect_timeout
        self.on_circuit_open = on_circuit_open
        self.on_circuit_close = on_circuit_close
        self.enable_broker_acks = enable_broker_acks

        ctx = zmq.Context.instance()

        # -- PUSH socket for sending messages --
        self._push = ctx.socket(zmq.PUSH)
        self._push.connect(f"tcp://{broker_host}:{push_port}")

        # -- SUB socket for receiving ACKs back from broker --
        self._sub = ctx.socket(zmq.SUB)
        self._sub.connect(f"tcp://{broker_host}:{ack_port}")
        self._sub.setsockopt_string(zmq.SUBSCRIBE, f"acks.{self.client_id}")

        # -- Monitor socket for low-level events on PUSH --
        #    We want to know when the TCP handshake actually completes.
        self._monitor = self._push.get_monitor_socket()
        self._connected = False

        # In-flight tracking
        self._unacked = {}  # type: ignore  # msg_id → (envelope, last_send_time)
        self._lock = threading.Lock()
        self._stop = threading.Event()

        # Circuit breaker state
        self._circuit_open = False

        # Start background threads
        threading.Thread(
            target=self._monitor_events, daemon=True, name="Monitor"
        ).start()

        if self.enable_broker_acks:
            threading.Thread(
                target=self._ack_receiver, daemon=True, name="AckReceiver"
            ).start()
            threading.Thread(
                target=self._resender, daemon=True, name="Resender"
            ).start()
            threading.Thread(
                target=self._backpressure_watchdog, daemon=True, name="Watchdog"
            ).start()

        # Block until we see a connect event (or timeout)
        self._wait_for_connection()

    def _wait_for_connection(self):
        """
        Block until the PUSH socket reports ZMQ_EVENT_CONNECTED
        (i.e. TCP handshake done), or raise ConnectionTimeoutError.
        """
        deadline = time.time() + self.connect_timeout
        while time.time() < deadline:
            if self._connected:
                return
            time.sleep(0.01)
        raise ConnectionTimeoutError(
            f"Could not connect to broker within {self.connect_timeout}s"
        )

    def publish(self, topic: str, payload: bytes) -> str:
        """
        Enqueue and send a message.

        Parameters
        ----------
        topic : str
            The topic to which the message should be published.
        payload : bytes
            The message payload to be sent.

        Raises
        ------
        CircuitOpenError
            If the circuit is open (broker appears down) and enable_broker_acks is True.
        ConnectionTimeoutError
            If the initial connection to the broker times out.
        """
        # Ensure we're connected before sending
        if not self._connected:
            # you may choose to block here or to fail fast
            self._wait_for_connection()

        if self._circuit_open:
            raise CircuitOpenError("Circuit is open: broker unavailable")

        if isinstance(payload, str):
            payload = payload.encode()

        msg_id = uuid.uuid4().hex
        envelope = [self.client_id.encode(), topic.encode(), msg_id.encode(), payload]

        if self.enable_broker_acks:
            # Back-pressure: block until there's capacity or circuit opens
            while True:
                with self._lock:
                    count = len(self._unacked)
                if count < self.max_unacked:
                    break
                if self._circuit_open:
                    raise CircuitOpenError("Circuit opened while waiting for capacity")
                time.sleep(0.00001)

            # Record & send
            with self._lock:
                self._unacked[msg_id] = (envelope, time.time())

        self._push.send_multipart(envelope)
        return msg_id

    def _ack_receiver(self):
        """Drop ACKed msg_ids out of the in-flight map."""
        while not self._stop.is_set():
            try:
                _, msgid = self._sub.recv_multipart(flags=zmq.NOBLOCK)
                mid = msgid.decode()
                with self._lock:
                    self._unacked.pop(mid, None)
            except zmq.Again:
                time.sleep(0.001)

    def _resender(self):
        """Retransmit any message older than ack_timeout."""
        while not self._stop.is_set():
            now = time.time()
            to_resend = []
            with self._lock:
                for mid, (env, ts) in list(self._unacked.items()):
                    if now - ts > self.ack_timeout:
                        to_resend.append(mid)
                        self._unacked[mid] = (env, now)
            for mid in to_resend:
                env, _ = self._unacked[mid]
                self._push.send_multipart(env)
            time.sleep(self.ack_timeout / 2)

    def _monitor_events(self):
        """
        Listen for ZMQ_EVENT_CONNECTED / DISCONNECTED.
        Updates self._connected and triggers circuit-close on reconnect.
        """
        while not self._stop.is_set():
            evt = self._monitor.recv_multipart()
            event = int.from_bytes(evt[0][:2], "little")
            if event == zmq.EVENT_CONNECTED:
                # Broker reachable at TCP level
                self._connected = True
                if self._circuit_open:
                    self._circuit_open = False
                    logger.warning("Circuit closed: broker reconnected")
                    if self.on_circuit_close:
                        self.on_circuit_close()
            elif event == zmq.EVENT_DISCONNECTED:
                self._connected = False
            time.sleep(0.01)

    def _backpressure_watchdog(self):
        """
        If in-flight window stays full for backpressure_timeout,
        trip the circuit (fail fast) and call on_circuit_open().
        """
        start_ts = None
        while not self._stop.is_set():
            with self._lock:
                count = len(self._unacked)
            if count >= self.max_unacked:
                if start_ts is None:
                    start_ts = time.time()
                elif time.time() - start_ts >= self.backpressure_timeout:
                    if not self._circuit_open:
                        self._circuit_open = True
                        logger.error("Circuit opened: sustained back-pressure")
                        if self.on_circuit_open:
                            self.on_circuit_open()
                    return
            else:
                start_ts = None
            time.sleep(0.1)

    @property
    def is_connected(self) -> bool:
        """True if TCP/ZeroMQ handshake with broker succeeded."""
        return self._connected

    @property
    def circuit_open(self) -> bool:
        return self._circuit_open

    def close(self):
        """Stop background threads and close sockets."""
        self._stop.set()
        # allow threads to wind down
        time.sleep(max(self.ack_timeout, self.backpressure_timeout))
        self._push.close(0)
        self._sub.close(0)
        self._monitor.close(0)
