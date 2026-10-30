"""Keyboard frames for the main chip's panel bus.

Measured on stock 5.0.0.2084 in Renode. Subcommand 0x05 is a key down and
0x06 is a key up. The key index is the low id byte. Stock firmware sounds
index n as MIDI note n+48, checked for 0, 7, 12 and 24. After boot the bus
device slot already points at the keyboard object, so the chip nibble is
not what selects it.
"""

from __future__ import annotations

NOTE_BASE = 48
SHIFT_ID = 0x0804
# Arp/Range. The button handler sends this id to the range editor, or to the
# sequencer mod-track path when the sequencer is on. That is the Oct | Mod
# button: it changes arp range, and it selects a seq mod track.
OCT_MOD_ID = 0x0401


def stock_note(index: int) -> int:
    if not 0 <= index <= 24:
        raise ValueError(f"key index {index} is outside 0..24")
    return NOTE_BASE + index


def key_frame(index: int, down: bool, velocity: int = 100) -> list[int]:
    """One 8-byte panel frame. Velocity is the low 7 bits; a release sends 0."""
    stock_note(index)
    value = (velocity & 0x7F) if down else 0
    body = [0x00, 0x05 if down else 0x06, 0x00, index, (value >> 8) & 0xFF, value & 0xFF]
    data = [0xAA, *body]
    return data + [sum(data) & 0xFF]


def button_frame(ident: int, down: bool) -> list[int]:
    """Chip 2 button edge. Down value is 0; up value is 0x08."""
    if not 0 <= ident <= 0xFFFF:
        raise ValueError(f"button id {ident} does not fit in 16 bits")
    value = 0 if down else 0x08
    body = [0x20, 0x01 if down else 0x02, (ident >> 8) & 0xFF, ident & 0xFF,
            (value >> 8) & 0xFF, value & 0xFF]
    data = [0xAA, *body]
    return data + [sum(data) & 0xFF]
