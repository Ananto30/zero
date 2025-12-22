import asyncio
from typing import Any, Tuple

from zero.encoder import Encoder

# 4-byte length prefix, 4 should be enough as it limits msg size to 4GB
LENGTH_PREFIX_SIZE = 4
# 4-byte request ID (uint32) for request-response correlation
# Per-connection lock ensures sequential requests, so 4 bytes is sufficient
REQUEST_ID_SIZE = 4
# 1-byte error flag to indicate if response is an error
ERROR_FLAG_SIZE = 1


async def read_frame(reader: asyncio.StreamReader) -> Tuple[bytes, bytes, bool]:
    """
    Read a frame from the stream.

    Frame format: [4-byte length][4-byte request_id][1-byte error_flag][encoded payload]

    Returns
    -------
    Tuple[bytes, bytes, bool]
        (request_id, encoded_payload_bytes, is_error)
    """
    try:
        header = await reader.readexactly(LENGTH_PREFIX_SIZE)
        length = int.from_bytes(header, "big")

        # Read request ID
        request_id = await reader.readexactly(REQUEST_ID_SIZE)

        # Read error flag
        error_flag_byte = await reader.readexactly(ERROR_FLAG_SIZE)
        is_error = error_flag_byte[0] != 0

        # Read remaining payload (length includes request ID and error flag)
        payload_size = length - REQUEST_ID_SIZE - ERROR_FLAG_SIZE
        payload = await reader.readexactly(payload_size)

        # Return raw payload bytes, not decoded, and error flag
        return request_id, payload, is_error
    except asyncio.IncompleteReadError as e:
        raise ConnectionError("Connection closed while reading frame") from e


async def write_frame(
    writer: asyncio.StreamWriter,
    obj: Any,
    encoder: Encoder,
    request_id: bytes,
    is_error: bool = False,
) -> None:
    """
    Write a frame to the stream.

    Frame format: [4-byte length][4-byte request_id][1-byte error_flag][encoded payload]

    Parameters
    ----------
    writer : asyncio.StreamWriter
    obj : Any
        Object to encode and send
    encoder : Encoder
    request_id : bytes
        4-byte request ID for request-response correlation
    is_error : bool
        Whether this response is an error
    """
    payload = encoder.encode(obj)
    error_flag = bytes([1 if is_error else 0])
    # Length includes request ID, error flag, and payload
    total_length = REQUEST_ID_SIZE + ERROR_FLAG_SIZE + len(payload)
    frame = (
        total_length.to_bytes(LENGTH_PREFIX_SIZE, "big")
        + request_id
        + error_flag
        + payload
    )
    writer.write(frame)
    await writer.drain()
