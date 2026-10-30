"""Print the offline release recipe. Do not store the image or flash a device.

Builds the mode image in memory from the SuperFreaker file in Downloads,
checks every written range, and prints the hashes and the manifest.
The payload bytes stay in this process.

    python scripts/release_recipe.py
"""

from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

from firmware.boundaries import PATCH_MANIFEST  # noqa: E402
from firmware.coexist import placement_ok  # noqa: E402
from firmware.triad import MODE_CAVE, changed_spans  # noqa: E402
from scripts.boot_triad import SUPER, STOCK, build  # noqa: E402
from scripts.inspect_firmware import load_mff, payload  # noqa: E402


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _rev(path: Path) -> str:
    if not (path / ".git").exists():
        return "absent"
    result = subprocess.run(
        ["git", "-C", str(path), "rev-parse", "HEAD"],
        capture_output=True, text=True, check=False,
    )
    return result.stdout.strip() or "unknown"


def _head() -> str:
    result = subprocess.run(
        ["git", "-C", str(_ROOT), "rev-parse", "HEAD"],
        capture_output=True, text=True, check=False,
    )
    return result.stdout.strip() or "unknown"


def _clang() -> str:
    compiler = Path(r"C:\Program Files\LLVM\bin\clang.exe")
    if not compiler.is_file():
        return "absent"
    result = subprocess.run(
        [str(compiler), "--version"],
        capture_output=True, text=True, check=False,
    )
    line = result.stdout.splitlines()
    return line[0] if line else "unknown"


def main() -> int:
    base, patched = build()
    spans = changed_spans(base, patched)
    for start, end in spans:
        if not placement_ok(start, end):
            raise SystemExit(f"patch overlaps a reserved range at 0x{start:08X}")
    stock = payload(load_mff(STOCK)[2][0][1])
    super_payload = payload(load_mff(SUPER)[2][0][1])
    print(f"commit {_head()}")
    print(f"clang {_clang()}")
    print(f"microfreak-emu {_rev(_ROOT / 'third_party' / 'microfreak-emu')}")
    print(f"microfreak-tools {_rev(_ROOT / 'third_party' / 'microfreak-tools')}")
    print(f"stock container {_sha256(STOCK.read_bytes())}")
    print(f"stock payload {_sha256(stock)} {len(stock)} bytes")
    print(f"superfreaker container {_sha256(SUPER.read_bytes())}")
    print(f"superfreaker payload {_sha256(super_payload)} {len(super_payload)} bytes")
    print(f"mode image {_sha256(patched)} {len(patched)} bytes")
    print(f"mode code origin 0x{MODE_CAVE:08X}")
    def covered(start: int, end: int) -> bool:
        return any(
            int(item["start"]) <= start and end <= int(item["end"])
            for item in PATCH_MANIFEST
        )

    outside = [(start, end) for start, end in spans if not covered(start, end)]
    if outside:
        for start, end in outside:
            print(f"bytes outside the manifest: 0x{start:08X}-0x{end:08X}")
        return 1
    print("manifest:")
    for item in PATCH_MANIFEST:
        print(f"  0x{int(item['start']):08X}-0x{int(item['end']):08X} {item['what']}")
    print(f"differing spans inside the manifest: {len(spans)}")
    print("payload stored: no")
    print("device write: no")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
