"""Static safety boundaries for a MicroFreak application patch.

These addresses come from the public microfreak-emu notes for firmware
5.0.0.2084. The stock and SuperFreaker hashes below were checked against
the user's files. Both images have been booted under Renode. The patch
manifest lists the triad hook's three ranges and no firmware bytes.

No function here writes a device.
"""

from __future__ import annotations

# Inclusive start, exclusive end.
BOOTLOADER = (0x08000000, 0x08008000)
FACTORY_DATA = (0x08008000, 0x0800C000)
APPLICATION = (0x0800C000, 0x08080000)

# Tail of speech bank 4 after its last word is retired. Re-measured on
# SuperFreaker 0.1.2: that word is 258 bytes, and the region ends at
# 0x0807B367, which is 259 bytes of room. See docs/SUPERFREAKER.md.
SPEECH_CODE_CAVE = (0x0807B264, 0x0807B367)

# Checked against the user's MicroFreak_Firmware_Update_5_0_0_2084.mff.
# The container hash is the whole .mff. The payload hash is the main
# application with Arturia's 64-byte header and trailing XOR removed.
STOCK_MFF_SHA256 = (
    "c2b405e3c8565b7b73b4dd06522559458190082a8ba633cc5f1bcc43dc64332c"
)
STOCK_PAYLOAD_SHA256 = (
    "54be2e0b695e2279602513e1a9ed39906408ba221a45e782b61273f0ef55d15f"
)
STOCK_PAYLOAD_SIZE = 473695
SUPERFREAKER_MFF_SHA256 = (
    "e596126d4b60328b2197448d34fe8a994f5e3761d517b828626992a4eb5d20dc"
)
SUPERFREAKER_PAYLOAD_SHA256 = (
    "00977cbb023f680500ab1c151342a7df5f462d9355e408e8c59b96e2d12c8c19"
)

# Ranges a triad image changes. Lengths only: no firmware bytes.
# The hook call, bank 4's size word, and the code in the retired word.
PATCH_MANIFEST: list[dict[str, object]] = [
    {"start": 0x080478EA, "end": 0x080478EE, "what": "bl to the triad hook"},
    {"start": 0x0807885C, "end": 0x08078860, "what": "bank 4 size, last word retired"},
    {"start": 0x0807B264, "end": 0x0807B2D2, "what": "major-triad hook"},
]


def cave_size() -> int:
    start, end = SPEECH_CODE_CAVE
    return end - start


def protected(address: int) -> bool:
    for start, end in (BOOTLOADER, FACTORY_DATA):
        if start <= address < end:
            return True
    return False
