"""Deterministic Orchid-style chord spelling.

Interval content follows the published Orchid chord model recorded in
ChoralRoot's chord-name notes: diminished, minor, major and suspended
triads, the three two-key combinations (augmented, power, minor-add4),
and the extensions 6, minor-seventh, major-seventh and major-ninth.

This module is a fresh implementation of those musical rules. It does not
include ChoralRoot source. ChoralRoot is GPL-3; this project is not a
derivative of that code.

A root with no quality selected spells a major triad. That is a deliberate
MicroFreak departure from the Orchid, which plays a single note until a
quality key is held. See docs/DECISIONS.md.
"""

from __future__ import annotations

from enum import IntEnum, IntFlag


class Quality(IntEnum):
    DIM = 1
    MIN = 2
    MAJ = 3
    SUS = 4
    AUG = 5
    POW = 6
    MIN4 = 7


class Ext(IntFlag):
    NONE = 0
    SIXTH = 1
    MIN7 = 2
    MAJ7 = 4
    NINTH = 8


# Semitone sets. The perfect fifth is stored with the triad and is the first
# tone dropped when a chord has to fit in four voices.
QUALITY_INTERVALS: dict[Quality, tuple[int, ...]] = {
    Quality.DIM: (0, 3, 6),
    Quality.MIN: (0, 3, 7),
    Quality.MAJ: (0, 4, 7),
    Quality.SUS: (0, 5, 7),
    Quality.AUG: (0, 4, 8),
    Quality.POW: (0, 7, 12),
    Quality.MIN4: (0, 3, 5),
}

EXT_INTERVALS: dict[Ext, int] = {
    Ext.SIXTH: 9,
    Ext.MIN7: 10,
    Ext.MAJ7: 11,
    Ext.NINTH: 14,
}

SIXTH_ABOVE_SEVENTH = 21

# How badly a tone wants to survive four-voice reduction. Higher stays.
SCORE_ROOT = 100
SCORE_QUALITY = 90
SCORE_SEVENTH = 75
SCORE_NINTH = 65
SCORE_SIXTH = 55
SCORE_FIFTH = 20

NOTE_NAMES = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")

# Key Mode, relative to the tonic. Low 3 bits are a Quality. Bit 3 means the
# root moves down a semitone, bit 4 means it moves up. Major degree 1 is the
# measured Orchid case (C# in C becomes C suspended). The other chromatic
# degrees use the same published table.
KEYMAP: dict[str, tuple[int, ...]] = {
    "major": (3, 12, 2, 12, 2, 3, 20, 3, 12, 2, 12, 1),
    "minor": (2, 12, 1, 3, 12, 2, 12, 2, 3, 20, 3, 12),
}

_SECRET = {
    Quality.MAJ: Quality.AUG,
    Quality.MIN: Quality.MIN4,
    Quality.DIM: Quality.POW,
}

_TRIAD = (Quality.DIM, Quality.MIN, Quality.MAJ)


def resolve_quality(stack: tuple[Quality, ...] | list[Quality]) -> Quality:
    """Pick one quality from keys held, most recent first.

    Suspended plus exactly one of major, minor or diminished becomes the
    matching combination chord. Two conflicting triads: the later one wins.
    An empty stack is major.
    """
    if not stack:
        return Quality.MAJ
    sus = Quality.SUS in stack
    triads = [q for q in stack if q in _TRIAD]
    if sus and triads:
        return _SECRET[triads[-1]]
    if sus:
        return Quality.SUS
    return triads[-1]


def key_mode_choice(mode: str, root_pc: int, tonic_pc: int) -> tuple[Quality, int]:
    """Return (quality, root-semitone-shift) for one scale degree."""
    table = KEYMAP[mode]
    degree = (root_pc - tonic_pc) % 12
    cell = table[degree]
    quality = Quality(cell & 7)
    if cell & 16:
        shift = 1
    elif cell & 8:
        shift = -1
    else:
        shift = 0
    return quality, shift


def _tones(quality: Quality, ext: Ext, sixth_up: bool) -> list[tuple[int, int]]:
    """Interval above the root, and how important it is to keep."""
    found: dict[int, int] = {}

    def put(interval: int, score: int) -> None:
        found[interval] = max(score, found.get(interval, 0))

    for interval in QUALITY_INTERVALS[quality]:
        if interval == 0:
            score = SCORE_ROOT
        elif interval == 7 and quality != Quality.POW:
            score = SCORE_FIFTH
        else:
            score = SCORE_QUALITY
        put(interval, score)

    if ext & Ext.SIXTH:
        interval = EXT_INTERVALS[Ext.SIXTH]
        if sixth_up and (ext & (Ext.MIN7 | Ext.MAJ7)):
            interval = SIXTH_ABOVE_SEVENTH
        put(interval, SCORE_SIXTH)
    if ext & Ext.MIN7:
        put(EXT_INTERVALS[Ext.MIN7], SCORE_SEVENTH)
    if ext & Ext.MAJ7:
        put(EXT_INTERVALS[Ext.MAJ7], SCORE_SEVENTH)
    if ext & Ext.NINTH:
        put(EXT_INTERVALS[Ext.NINTH], SCORE_NINTH)
    return list(found.items())


def apply_inversion(notes: list[int], steps: int) -> list[int]:
    """Rotate voicing. Positive raises the lowest note an octave.

    Rotation stops at the MIDI range edge instead of dropping the tone.
    """
    voiced = sorted(notes)
    if not voiced or steps == 0:
        return voiced
    if steps > 0:
        for _ in range(steps):
            if voiced[0] + 12 > 127:
                break
            voiced[0] += 12
            voiced.sort()
    else:
        for _ in range(-steps):
            if voiced[-1] < 12:
                break
            voiced[-1] -= 12
            voiced.sort()
    return voiced


def reduce_voices(scored: list[tuple[int, int]], limit: int | None) -> list[int]:
    """Keep at most `limit` MIDI notes. Ties keep the lower pitch."""
    if limit is None or len(scored) <= limit:
        return sorted(note for note, _score in scored)
    ranked = sorted(scored, key=lambda item: (-item[1], item[0]))
    return sorted(note for note, _score in ranked[:limit])


def spell(
    root: int,
    quality: Quality = Quality.MAJ,
    ext: Ext = Ext.NONE,
    *,
    sixth_up: bool = False,
    inversion: int = 0,
    voice_limit: int | None = 4,
) -> list[int]:
    """Spell one chord. `voice_limit=None` keeps every tone (external MIDI)."""
    if not 0 <= root <= 127:
        raise ValueError(f"root {root} is outside MIDI 0..127")
    scored: list[tuple[int, int]] = []
    for interval, score in _tones(quality, ext, sixth_up):
        note = root + interval
        if 0 <= note <= 127:
            scored.append((note, score))
    return apply_inversion(reduce_voices(scored, voice_limit), inversion)


def chord_symbol(root: int, quality: Quality, ext: Ext = Ext.NONE) -> str:
    """Short label for logs and the OLED stand-in. Display only."""
    name = NOTE_NAMES[root % 12]
    if quality is Quality.MAJ and ext == Ext.NONE:
        return name
    if quality is Quality.MAJ and ext == (Ext.MIN7 | Ext.NINTH):
        return f"{name}9"
    if quality is Quality.MAJ and ext == (Ext.MAJ7 | Ext.NINTH):
        return f"{name}maj9"
    if quality is Quality.MIN and ext == (Ext.MIN7 | Ext.NINTH):
        return f"{name}m9"
    if quality is Quality.MIN and ext == Ext.MIN7:
        return f"{name}m7"
    if quality is Quality.MAJ and ext == Ext.MAJ7:
        return f"{name}maj7"
    if quality is Quality.MAJ and ext == Ext.MIN7:
        return f"{name}7"
    qual = {
        Quality.DIM: "dim",
        Quality.MIN: "m",
        Quality.MAJ: "",
        Quality.SUS: "sus",
        Quality.AUG: "aug",
        Quality.POW: "5",
        Quality.MIN4: "madd4",
    }[quality]
    tags: list[str] = []
    if ext & Ext.SIXTH:
        tags.append("6")
    if ext & Ext.MIN7:
        tags.append("7")
    if ext & Ext.MAJ7:
        tags.append("maj7")
    if ext & Ext.NINTH:
        tags.append("9")
    extra = "" if not tags else "".join(tags) if len(tags) == 1 else "+" + "+".join(tags)
    return f"{name}{qual}{extra}"
