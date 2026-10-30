"""Write a MIDI Control Center .mff for the mode image.

Copies the SuperFreaker container and replaces the main application.
The OLED, matrix, keyboard, and wavetable images are copied unchanged.
The downloads are not modified, and nothing is written to a device.
The .mff is gitignored. It is not stored in this repository.

    python scripts/pack_mff.py
    python scripts/pack_mff.py C:/Users/thisi/Downloads/micro-orchid.mff
"""

from __future__ import annotations

import hashlib
import sys
import zipfile
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

from scripts.boot_triad import SUPER, build  # noqa: E402
from scripts.inspect_firmware import HEADER, load_mff, payload  # noqa: E402

MAIN = "nanowave_main__fw5_0_0_2084__2023_05_30.bin"
DEFAULT_OUT = Path(r"C:\Users\thisi\Downloads\micro-orchid.mff")


def _xor(data: bytes) -> int:
    value = 0
    for byte in data:
        value ^= byte
    return value


def replace_main(blob: bytes, patched: bytes) -> bytes:
    """New main image. Header byte 1 and the last byte are the payload XOR."""
    if len(blob) != HEADER + len(patched) + 1:
        raise SystemExit(
            f"main image is {len(blob)} bytes and the payload is {len(patched)}"
        )
    header = bytearray(blob[:HEADER])
    header[1] = _xor(patched)
    return bytes(header) + patched + bytes((header[1],))


def pack(destination: Path) -> str:
    _base, patched = build()
    _raw, info, images = load_mff(SUPER)
    main_blob = images[0][1]
    original = main_blob[HEADER:-1]
    if replace_main(main_blob, original) != main_blob:
        raise SystemExit("the checksum wrap does not reproduce the SuperFreaker image")
    if payload(replace_main(main_blob, patched)) != patched:
        raise SystemExit("the packed payload does not match the mode image")
    destination = destination.resolve()
    if destination in {SUPER.resolve(), Path(r"C:\Users\thisi\Downloads\MicroFreak_Firmware_Update_5_0_0_2084.mff").resolve()}:
        raise SystemExit("refusing to overwrite a downloaded firmware file")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(SUPER) as source, zipfile.ZipFile(destination, "w") as out:
        for item in source.infolist():
            data = source.read(item.filename)
            if item.filename == MAIN:
                data = replace_main(data, patched)
            info_item = zipfile.ZipInfo(filename=item.filename, date_time=item.date_time)
            info_item.compress_type = zipfile.ZIP_STORED
            info_item.external_attr = item.external_attr
            info_item.flag_bits = item.flag_bits
            out.writestr(info_item, data)
    packed_raw, packed_info, packed_images = load_mff(destination)
    if packed_info != info:
        raise SystemExit("info.json changed")
    if payload(packed_images[0][1]) != patched:
        raise SystemExit("the written main image does not match the mode")
    for number, (name, blob) in images.items():
        if number == 0:
            continue
        if packed_images[number] != (name, blob):
            raise SystemExit(f"image {number} {name} was not copied unchanged")
    return hashlib.sha256(packed_raw).hexdigest()


def main() -> int:
    destination = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_OUT
    digest = pack(destination)
    _base, patched = build()
    print(f"wrote {destination}")
    print(f"mff sha256 {digest}")
    print(f"payload sha256 {hashlib.sha256(patched).hexdigest()}")
    print("downloads were not modified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
