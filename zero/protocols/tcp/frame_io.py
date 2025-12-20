import asyncio
from typing import Any

from zero.encoder import Encoder

# 4-byte length prefix, 4 should be enough as it limits msg size to 4GB
LENGTH_PREFIX_SIZE = 4


async def read_frame(reader: asyncio.StreamReader, encoder: Encoder) -> dict:
    try:
        header = await reader.readexactly(LENGTH_PREFIX_SIZE)
        length = int.from_bytes(header, "big")
        payload = await reader.readexactly(length)
        return encoder.decode(payload)
    except asyncio.IncompleteReadError as e:
        raise ConnectionError("Connection closed while reading frame") from e


async def write_frame(writer: asyncio.StreamWriter, obj: Any, encoder: Encoder) -> None:
    payload = encoder.encode(obj)
    writer.write(len(payload).to_bytes(LENGTH_PREFIX_SIZE, "big") + payload)
    await writer.drain()
