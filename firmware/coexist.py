"""Keep an Orchid patch off bytes SuperFreaker already changed.

`superfreaker_v0_1_2_ranges.json` is addresses and lengths measured from the
user's stock 5.0.0.2084 image and SuperFreaker 0.1.2. It contains no firmware
bytes. A range is half-open: start is included, end is not.

The speech-vocabulary cave SuperFreaker left alone is still only 259 bytes.
Landing there does not collide with SuperFreaker. The chord engine does not
fit in that one word; the mode image retires twenty-one bank-4 words instead.
"""

from __future__ import annotations

import json
from pathlib import Path

MAP_PATH = Path(__file__).with_name("superfreaker_v0_1_2_ranges.json")

# Their rewritten utility and effect code. Unchanged gaps inside this window
# are still their code. Do not plant an Orchid hook in a gap.
SUPERFREAKER_WINDOW = (0x0802B8F0, 0x0802EF30)

# Boot banner. Overwriting it would erase the SuperFreaker version line.
BANNER = (0x080757AC, 0x080757CC)

# Shift-lock text and the handler SuperFreaker replaced. Orchid's
# Shift+OCT|MOD toggle must not patch this site.
SHIFT_LOCK = (0x080387A4, 0x08038A80)


def load_map(path: Path | None = None) -> dict:
    return json.loads((path or MAP_PATH).read_text(encoding="utf-8"))


def changed_ranges(record: dict | None = None) -> list[tuple[int, int]]:
    record = record if record is not None else load_map()
    return [(int(item["start"]), int(item["end"])) for item in record["ranges"]]


def overlaps(start: int, end: int, record: dict | None = None) -> list[tuple[int, int]]:
    """Return recorded SuperFreaker ranges that intersect [start, end)."""
    if end < start:
        raise ValueError("end is before start")
    hits = []
    for left, right in changed_ranges(record):
        if start < right and end > left:
            hits.append((left, right))
    return hits


def reserved(start: int, end: int) -> list[str]:
    """Named regions an Orchid patch must leave alone even when bytes match."""
    names = (
        ("superfreaker-window", SUPERFREAKER_WINDOW),
        ("banner", BANNER),
        ("shift-lock", SHIFT_LOCK),
    )
    return [name for name, (left, right) in names if start < right and end > left]


def placement_ok(start: int, end: int, record: dict | None = None) -> bool:
    return not overlaps(start, end, record) and not reserved(start, end)
