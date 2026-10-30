"""Compare a stock MicroFreak .mff with another build.

Prints image hashes and the main-application byte ranges that differ.
`--write` stores addresses and lengths only. It does not copy firmware
bytes into the repository.

    python scripts/inspect_firmware.py STOCK.mff OTHER.mff
    python scripts/inspect_firmware.py STOCK.mff OTHER.mff --check firmware/superfreaker_v0_1_2_ranges.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import zipfile
from pathlib import Path

HEADER = 0x40
BASE = 0x0800C000
ROLES = {
    0: "main",
    1: "oled",
    2: "matrix",
    3: "keyboard",
    4: "wavetables",
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_mff(path: Path) -> tuple[bytes, dict, dict[int, tuple[str, bytes]]]:
    raw = path.read_bytes()
    with zipfile.ZipFile(path) as archive:
        info = json.loads(archive.read("info.json"))
        images = {}
        for image in info["images"]:
            number = int(image["image_num"])
            name = image["file_name"]
            images[number] = (name, archive.read(name))
    return raw, info, images


def payload(blob: bytes) -> bytes:
    return blob[HEADER:-1]


def changed_ranges(left: bytes, right: bytes) -> list[tuple[int, int]]:
    if len(left) != len(right):
        raise SystemExit(f"payload lengths differ: {len(left)} and {len(right)}")
    ranges: list[tuple[int, int]] = []
    start = None
    for index, (a, b) in enumerate(zip(left, right)):
        if a != b and start is None:
            start = index
        elif a == b and start is not None:
            ranges.append((BASE + start, BASE + index))
            start = None
    if start is not None:
        ranges.append((BASE + start, BASE + len(left)))
    return ranges


def report(stock_path: Path, other_path: Path) -> dict:
    stock_raw, stock_info, stock_images = load_mff(stock_path)
    other_raw, other_info, other_images = load_mff(other_path)
    stock_main = payload(stock_images[0][1])
    other_main = payload(other_images[0][1])
    ranges = changed_ranges(stock_main, other_main)
    images = []
    for number in sorted(set(stock_images) & set(other_images)):
        same = stock_images[number][1] == other_images[number][1]
        images.append({
            "image": number,
            "role": ROLES.get(number, "unknown"),
            "name": stock_images[number][0],
            "identical": same,
            "stock_payload_sha256": sha256(payload(stock_images[number][1])),
            "other_payload_sha256": sha256(payload(other_images[number][1])),
        })
    version_at = 0x080757AC - BASE
    return {
        "stock_file": stock_path.name,
        "other_file": other_path.name,
        "stock_version": stock_info.get("version_number"),
        "other_version": other_info.get("version_number"),
        "stock_mff_sha256": sha256(stock_raw),
        "other_mff_sha256": sha256(other_raw),
        "stock_payload_sha256": sha256(stock_main),
        "other_payload_sha256": sha256(other_main),
        "payload_size": len(stock_main),
        "changed_bytes": sum(end - start for start, end in ranges),
        "range_count": len(ranges),
        "ranges": [{"start": start, "end": end} for start, end in ranges],
        "images": images,
        "other_banner": other_main[version_at:version_at + 24].split(b"\x00", 1)[0].decode("ascii", "replace"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stock")
    parser.add_argument("other")
    parser.add_argument("--check", type=Path)
    parser.add_argument("--write", type=Path)
    args = parser.parse_args()
    found = report(Path(args.stock), Path(args.other))
    print(f"stock  {found['stock_file']}  {found['stock_mff_sha256']}")
    print(f"       payload {found['stock_payload_sha256']}  {found['payload_size']} bytes")
    print(f"other  {found['other_file']}  {found['other_mff_sha256']}")
    print(f"       payload {found['other_payload_sha256']}")
    print(f"banner {found['other_banner']!r}")
    print(f"main differs in {found['changed_bytes']} bytes across {found['range_count']} ranges")
    for image in found["images"]:
        state = "identical" if image["identical"] else "CHANGED"
        print(f"  image {image['image']} {image['role']}: {state}")
    if args.write:
        args.write.parent.mkdir(parents=True, exist_ok=True)
        args.write.write_text(json.dumps(found, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {args.write}")
    if args.check:
        recorded = json.loads(args.check.read_text(encoding="utf-8"))
        keys = (
            "stock_mff_sha256",
            "other_mff_sha256",
            "stock_payload_sha256",
            "other_payload_sha256",
            "changed_bytes",
            "ranges",
        )
        mismatches = [key for key in keys if recorded.get(key) != found[key]]
        if mismatches:
            print("recorded map does not match these files:", ", ".join(mismatches))
            return 1
        print(f"recorded map matches {args.check}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
