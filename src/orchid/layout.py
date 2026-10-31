"""25-key Orchid layout for the MicroFreak keyboard.

Index 0 is the leftmost physical key. Nothing here claims that a capacitive
scan code equals a MIDI note. The host maps an incoming note onto an index
only after a configured base note is subtracted. See docs/CONTROL-MAPPING.md.
"""

from __future__ import annotations

from enum import Enum

from orchid.chords import Ext, Quality


class Key(Enum):
    DIM = "dim"
    MIN = "min"
    MAJ = "maj"
    SUS = "sus"
    SIXTH = "sixth"
    MIN7 = "min7"
    MAJ7 = "maj7"
    NINTH = "ninth"
    INV_DOWN = "inv_down"
    INV_UP = "inv_up"
    BASS = "bass"
    ARP = "arp"


LAYOUT: tuple[Key, ...] = (
    Key.DIM,
    Key.MIN,
    Key.MAJ,
    Key.SUS,
    Key.SIXTH,
    Key.MIN7,
    Key.MAJ7,
    Key.NINTH,
    Key.INV_DOWN,
    Key.INV_UP,
    Key.BASS,
    Key.ARP,
)

MODIFIER_COUNT = len(LAYOUT)
ROOT_COUNT = 13
KEY_COUNT = MODIFIER_COUNT + ROOT_COUNT

# Right-hand roots are C4 through C5 when octave shift is 0.
ROOT_BASE_NOTE = 60

QUALITY_KEYS = {
    Key.DIM: Quality.DIM,
    Key.MIN: Quality.MIN,
    Key.MAJ: Quality.MAJ,
    Key.SUS: Quality.SUS,
}

EXTENSION_KEYS = {
    Key.SIXTH: Ext.SIXTH,
    Key.MIN7: Ext.MIN7,
    Key.MAJ7: Ext.MAJ7,
    Key.NINTH: Ext.NINTH,
}


def physical_key(index: int) -> tuple[str, Key | int]:
    """Map a physical index 0..24 to ('mod', Key) or ('root', pitch-class offset)."""
    if not 0 <= index < KEY_COUNT:
        raise ValueError(f"key index {index} is outside 0..{KEY_COUNT - 1}")
    if index < MODIFIER_COUNT:
        return ("mod", LAYOUT[index])
    return ("root", index - MODIFIER_COUNT)


def root_note(index: int, octave: int = 0) -> int:
    """MIDI note for a right-hand key. Index 12 is C4 at octave 0."""
    _kind, offset = physical_key(index)
    if _kind != "root":
        raise ValueError(f"key {index} is a modifier, not a root")
    note = ROOT_BASE_NOTE + int(offset) + 12 * octave
    if not 0 <= note <= 127:
        raise ValueError(f"root note {note} is outside MIDI 0..127")
    return note
