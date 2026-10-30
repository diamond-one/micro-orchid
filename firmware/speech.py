"""Speech-vocabulary descriptor on the 5.0.0.2084 main image.

The five banks are a packed bitstream. Code reaches them through this
table, not through a PC-relative load of an address inside a bank.
Shortening the last bank's size, on a word boundary, is how the tail
becomes writable. The existing 259-byte cave is that tail after the last
word of bank 4 is retired.

This module only reads the descriptor. It does not decode the bitstream
and it does not write a device.
"""

from __future__ import annotations

import struct

TABLE = 0x08078838
REGION_END = 0x0807B367
BANK_COUNT = 5


def banks(image: bytes, base: int) -> list[tuple[int, int]]:
    """Five `(pointer, size)` pairs from the vocabulary descriptor."""
    offset = TABLE - base
    if offset < 0 or offset + BANK_COUNT * 8 > len(image):
        raise ValueError("speech table is outside the image")
    return [
        struct.unpack_from("<II", image, offset + 8 * index)
        for index in range(BANK_COUNT)
    ]
