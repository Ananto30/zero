import asyncio
from typing import Any, Tuple

from zero.encoder import Encoder

# 4-byte length prefix, 4 should be enough as it limits msg size to 4GB
LENGTH_PREFIX_SIZE = 4
# 4-byte request ID (uint32) for request-response correlation
# Per-connection lock ensures sequential requests, so 4 bytes is sufficient
REQUEST_ID_SIZE = 4


async def read_frame(reader: asyncio.StreamReader) -> Tuple[bytes, bytes]:
    """
    Read a frame from the stream.

    Frame format: [4-byte length][4-byte request_id][encoded payload]

    Returns
    -------
    Tuple[bytes, bytes]
        (request_id, encoded_payload_bytes)
    """
    try:
        header = await reader.readexactly(LENGTH_PREFIX_SIZE)
        length = int.from_bytes(header, "big")

        # Read request ID
        request_id = await reader.readexactly(REQUEST_ID_SIZE)

        # Read remaining payload (length includes request ID)
        payload_size = length - REQUEST_ID_SIZE
        payload = await reader.readexactly(payload_size)

        # Return raw payload bytes, not decoded
        return request_id, payload
    except asyncio.IncompleteReadError as e:
        raise ConnectionError("Connection closed while reading frame") from e


async def write_frame(
    writer: asyncio.StreamWriter, obj: Any, encoder: Encoder, request_id: bytes
) -> None:
    """
    Write a frame to the stream.

    Frame format: [4-byte length][16-byte request_id][encoded payload]

    Parameters
    ----------
    writer : asyncio.StreamWriter
    obj : Any
        Object to encode and send
    encoder : Encoder
    request_id : bytes
        16-byte request ID for request-response correlation
    """
    payload = encoder.encode(obj)
    # Length includes both request ID and payload
    total_length = REQUEST_ID_SIZE + len(payload)
    frame = total_length.to_bytes(LENGTH_PREFIX_SIZE, "big") + request_id + payload
    writer.write(frame)
    await writer.drain()
