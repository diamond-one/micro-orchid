"""Measure unused spans in a MicroFreak main image.

Prints addresses and lengths only. Firmware bytes stay in the file you pass.

    python scripts/find_cave.py PATH.mff
"""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

from firmware.cave import gaps  # noqa: E402
from firmware.coexist import placement_ok  # noqa: E402
from firmware.speech import REGION_END, banks  # noqa: E402
from scripts.inspect_firmware import BASE, load_mff, payload  # noqa: E402


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: python scripts/find_cave.py PATH.mff", file=sys.stderr)
        return 2
    _raw, info, images = load_mff(Path(argv[1]))
    main_image = next(blob for number, (_name, blob) in images.items() if number == 0)
    image = payload(main_image)
    found = gaps(image, BASE)
    allowed = [gap for gap in found if placement_ok(gap.start, gap.end)]
    allowed.sort(key=lambda gap: gap.size, reverse=True)
    print(f"payload {len(image)} bytes, base 0x{BASE:08X}")
    print("speech banks (pointer, size), reached through the descriptor:")
    for index, (pointer, size) in enumerate(banks(image, BASE)):
        print(f"  bank {index}  0x{pointer:08X}  {size} bytes")
    tail = banks(image, BASE)[-1]
    print(
        f"bank 4 ends at 0x{tail[0] + tail[1]:08X}; "
        f"region end 0x{REGION_END:08X}"
    )
    print(
        "A span below was not reached from the vector table and was not "
        "loaded by a PC-relative literal. These spans still contain "
        "instructions. They are not a cave."
    )
    print(f"spans {len(found)}, accepted by the coexistence check {len(allowed)}")
    for gap in allowed[:20]:
        print(f"  0x{gap.start:08X}..0x{gap.end:08X}  {gap.size} bytes")
    if not allowed:
        print("no accepted span")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
