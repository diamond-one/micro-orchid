"""Static safety boundaries for a MicroFreak application patch.

These addresses come from the public microfreak-emu notes for firmware
5.0.0.2084. This repository has not executed that firmware. The patch
manifest stays empty until a stock image is present and a patch is built
from it.

No function here writes a device.
"""

from __future__ import annotations

# Inclusive start, exclusive end.
BOOTLOADER = (0x08000000, 0x08008000)
FACTORY_DATA = (0x08008000, 0x0800C000)
APPLICATION = (0x0800C000, 0x08080000)

# microfreak-tools patching.py: the only cave it documents is the tail of
# the speech vocabulary. Claimed, not re-measured against an image we hold.
SPEECH_CODE_CAVE = (0x0807B264, 0x0807B367)

# Payload identity published by microfreak-tools 0.1.0. The instruction
# file also quoted c2b405e3...; that digest was not checked, because no
# stock file is in this tree.
STOCK_PAYLOAD_SHA256 = (
    "54be2e0b695e2279602513e1a9ed39906408ba221a45e782b61273f0ef55d15f"
)
STOCK_PAYLOAD_SIZE = 473695
UNVERIFIED_INSTRUCTION_SHA256 = (
    "c2b405e3c8565b7b73b4dd06522559458190082a8ba633cc5f1bcc43dc64332c"
)

# Byte ranges this project has changed inside a firmware image.
# Empty on purpose.
PATCH_MANIFEST: list[dict[str, object]] = []


def cave_size() -> int:
    start, end = SPEECH_CODE_CAVE
    return end - start


def protected(address: int) -> bool:
    for start, end in (BOOTLOADER, FACTORY_DATA):
        if start <= address < end:
            return True
    return False
