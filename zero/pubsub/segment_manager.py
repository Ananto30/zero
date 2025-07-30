# segment_manager.py

import os
import struct
import zlib
from typing import Dict, List, Tuple

# ——————————————————————————————————————————————————————————————
# Constants tuning performance and rollover
# ——————————————————————————————————————————————————————————————
# Maximum size of each segment file before rotating (64 MiB)
SEGMENT_SIZE = 64 * 1024 * 1024
# Number of messages to buffer in memory before flushing to disk
BATCH_SIZE = 100
# How often (in messages) to record a sparse timestamp index entry
INDEX_EVERY_N = 1000


class SegmentWriter:
    """
    A single append-only segment with in-memory batching and sparse timestamp indexing.

    On append:
      • Record is formatted as:
          [ 4-byte length ][ 8-byte offset ][ 8-byte timestamp ][ payload bytes ][ 4-byte CRC32 ]
      • Appends go into a small in-memory batch to amortize syscalls
      • Every INDEX_EVERY_N messages, we record (timestamp, offset, file_pos) in a sparse index
      • When batch is full, we flush to disk in one go

    Attributes:
      path         - the file path of this segment (e.g. ".../<start_offset>.log")
      start_offset - global offset of the first record in this segment
      next_offset  - next global offset to assign
      write_pos    - current write position within the file
      batch        - list of pending record bytes
      ts_index     - sparse list of (timestamp, offset, file_pos) tuples
    """

    def __init__(self, topic_dir: str, start_offset: int):
        # File is named by its starting offset, zero-padded for lexicographic order
        filename = f"{start_offset:020d}.log"
        self.path = os.path.join(topic_dir, filename)
        os.makedirs(topic_dir, exist_ok=True)

        # Determine where to pick up: count existing records and find write_pos
        self.start_offset = start_offset
        self.next_offset, self.write_pos = self._initialize_offset()

        # Open file for read+write; pointer at end for appends
        mode = "r+b" if os.path.exists(self.path) else "w+b"
        self.fd = open(self.path, mode)
        self.fd.seek(self.write_pos)

        # In-memory buffers
        self.batch = []  # type: List[bytes]
        self.ts_index = []  # type: List[Tuple[int, int, int]]

    def _initialize_offset(self) -> Tuple[int, int]:
        """
        Scan the file to:
          1) Count how many records are present → next_offset
          2) Compute byte-position after the last record → write_pos

        This lets us resume writing from the correct place on startup.
        """
        count = 0
        pos = 0
        if not os.path.exists(self.path):
            return self.start_offset, 0

        with open(self.path, "rb") as f:
            while True:
                hdr = f.read(4)
                if not hdr:
                    break
                length = struct.unpack(">I", hdr)[0]
                # skip the record body (+4 bytes CRC)
                f.seek(length + 4, os.SEEK_CUR)
                count += 1
                pos = f.tell()

        # The next_offset = start_offset + count of existing records
        return self.start_offset + count, pos

    def append(self, payload: bytes, timestamp_ms: int):
        """
        Queue a new record.  If our in-memory batch reaches BATCH_SIZE,
        we flush it in one syscall for high throughput.
        """
        # Build the record: offset + timestamp + payload
        meta = struct.pack(">Q", self.next_offset) + struct.pack(">Q", timestamp_ms)
        record = meta + payload
        crc = struct.pack(">I", zlib.crc32(record) & 0xFFFFFFFF)
        full = struct.pack(">I", len(record)) + record + crc

        # Every INDEX_EVERY_N, remember a sparse index entry
        if (self.next_offset - self.start_offset) % INDEX_EVERY_N == 0:
            self.ts_index.append((timestamp_ms, self.next_offset, self.write_pos))

        # Enqueue and advance offset
        self.batch.append(full)
        self.next_offset += 1

        # Flush if we’ve accumulated enough
        if len(self.batch) >= BATCH_SIZE:
            self._flush_batch()

    def _flush_batch(self):
        """
        Write all pending records in one go and update write_pos.
        """
        data = b"".join(self.batch)
        self.fd.write(data)
        # Ensure data reaches the OS; actual disk flush is deferred for performance
        self.fd.flush()
        self.write_pos += len(data)
        self.batch.clear()

    def flush(self):
        """
        Exposed flush: writes any remaining batched records to disk.
        """
        if self.batch:
            self._flush_batch()

    def close(self):
        """
        Finalize this segment:
          • Flush any pending writes
          • Write the sparse timestamp index to `<start_offset>.tsindex`
          • Close file descriptor
        """
        self.flush()
        # Persist sparse index for possible fast seeks on restart
        idx_path = self.path.replace(".log", ".tsindex")
        with open(idx_path, "wb") as idxf:
            for ts, off, pos in self.ts_index:
                idxf.write(struct.pack(">QQQ", ts, off, pos))
        self.fd.close()

    def read_from_offset(self, start_offset: int) -> List[Tuple[int, int, bytes]]:
        """
        Scan this segment and return all (offset, timestamp, payload)
        for records with global offset >= start_offset.
        """
        if self.batch:
            self.flush()

        results = []
        with open(self.path, "rb") as f:
            while True:
                hdr = f.read(4)
                if not hdr:
                    break
                length = struct.unpack(">I", hdr)[0]
                body = f.read(length)
                f.read(4)  # skip CRC
                off = struct.unpack(">Q", body[0:8])[0]
                ts = struct.unpack(">Q", body[8:16])[0]
                payload = body[16:]
                if off >= start_offset:
                    results.append((off, ts, payload))
        return results

    def find_offset_from_timestamp(self, target_ts: int) -> int:
        """
        Find the first record in this segment whose timestamp >= target_ts.
        Returns its global offset, or `self.next_offset` if none found.
        """
        if self.batch:
            self.flush()

        # Optional optimization: use self.ts_index to seek into file,
        # but for simplicity we do a linear scan here.
        with open(self.path, "rb") as f:
            while True:
                hdr = f.read(4)
                if not hdr:
                    break
                length = struct.unpack(">I", hdr)[0]
                body = f.read(length)
                f.read(4)
                off = struct.unpack(">Q", body[0:8])[0]
                ts = struct.unpack(">Q", body[8:16])[0]
                if ts >= target_ts:
                    return off
        return self.next_offset


class SegmentManager:
    """
    Manages per-topic append-only logs composed of fixed-size segments.

    Features:
      • Segment rotation when a segment reaches SEGMENT_SIZE
      • In-memory batching for high write throughput
      • Sparse timestamp indexing for future fast seeks
      • Simple read-across-segments for offset- and timestamp-based replay
    """

    def __init__(self, base_dir: str = "logs"):
        """
        base_dir: root directory under which each topic has its own subdirectory.
        """
        self.base_dir = base_dir
        os.makedirs(base_dir, exist_ok=True)
        # Map: topic → list of SegmentWriter instances in ascending offset order
        self._segments: Dict[str, List[SegmentWriter]] = {}

        # Load existing segments from disk on startup
        for topic in os.listdir(base_dir):
            if os.path.isdir(os.path.join(base_dir, topic)):
                self._load_segments(topic)

    def _load_segments(self, topic: str):
        """
        Load existing segments for a topic from disk.
        This is called on startup to restore state.
        """
        topic_dir = os.path.join(self.base_dir, topic)
        if not os.path.exists(topic_dir):
            return

        # List all segment files, sorted by their starting offset
        files = sorted(
            [f for f in os.listdir(topic_dir) if f.endswith(".log")],
            key=lambda x: int(x[:-4]),  # strip ".log" and convert to int
        )
        for filename in files:
            start_offset = int(filename[:-4])  # strip ".log"
            seg_path = os.path.join(topic_dir, filename)
            seg_writer = SegmentWriter(topic_dir, start_offset)
            seg_writer.fd = open(seg_path, "r+b")  # reopen for read+write
            seg_writer.write_pos = seg_writer._initialize_offset()[
                1
            ]  # update write_pos
            self._segments.setdefault(topic, []).append(seg_writer)

    def append(self, topic: str, payload: bytes, timestamp_ms: int):
        """
        Append a message to the given topic log:
          1) Acquire or create the active segment writer
          2) Write the record (batched)
          3) If the segment exceeds SEGMENT_SIZE, rotate to a new segment
        """
        segs = self._segments.setdefault(topic, [])
        if not segs:
            # First segment starts at offset 0
            segs.append(SegmentWriter(os.path.join(self.base_dir, topic), 0))

        writer = segs[-1]
        writer.append(payload, timestamp_ms)

        # Rotate if this segment is “full”
        if writer.write_pos >= SEGMENT_SIZE:
            writer.close()
            # Next segment starts at the next global offset
            new_start = writer.next_offset
            segs.append(SegmentWriter(os.path.join(self.base_dir, topic), new_start))

    def read_from_offset(
        self, topic: str, start_offset: int
    ) -> List[Tuple[int, int, bytes]]:
        """
        Return all messages for `topic` with offset ≥ start_offset.
        Internally reads across all segments in order.
        """
        out = []
        for writer in self._segments.get(topic, []):
            out.extend(writer.read_from_offset(start_offset))
        return out

    def find_offset_from_timestamp(self, topic: str, timestamp_ms: int) -> int:
        """
        Find the earliest offset for `topic` whose timestamp ≥ timestamp_ms.
        Scans segments in order and returns the first match.
        """
        for writer in self._segments.get(topic, []):
            off = writer.find_offset_from_timestamp(timestamp_ms)
            # If this segment contained a matching record, its offset < next_offset
            if off < writer.next_offset:
                return off
        # No record matched → return the end of the last segment (i.e. next_offset)
        if topic in self._segments and self._segments[topic]:
            return self._segments[topic][-1].next_offset
        return 0

    def next_offset(self, topic: str) -> int:
        """
        Return the next global offset that will be assigned for the given topic.
        Broker uses this to know “what offset just got written?” after append.
        """
        segs = self._segments.get(topic)
        if not segs:
            return 0
        return segs[-1].next_offset
