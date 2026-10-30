"""Boot the triad image and compare its notes with the Python engine.

Builds a payload from SuperFreaker, retires bank 4's last word, and
places the major-triad hook. Writes that payload to a temp file.
Does not modify the downloaded .mff and does not write a device.

    python scripts/boot_triad.py
    python scripts/boot_triad.py --check
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "src"))

from firmware.coexist import placement_ok  # noqa: E402
from firmware.triad import (  # noqa: E402
    BANK4_SIZE_ADDR,
    HOOK_SITE,
    STARTUP_SP,
    VECTOR_SP,
    apply_mode,
    changed_spans,
    compile_mode,
)
from orchid.engine import Engine  # noqa: E402
from orchid.layout import Key  # noqa: E402
from scripts.inspect_firmware import load_mff, payload  # noqa: E402

STOCK = Path(r"C:\Users\thisi\Downloads\MicroFreak_Firmware_Update_5_0_0_2084.mff")
SUPER = Path(r"C:\Users\thisi\Downloads\superfreaker_v0_1_2_5_0_0_2084.mff")
ROOT_NOTE = 60
VELOCITY = 100


def build() -> tuple[bytes, bytes]:
    code = compile_mode()
    stock = payload(load_mff(STOCK)[2][0][1])
    base = payload(load_mff(SUPER)[2][0][1])
    for address, length in (
        (HOOK_SITE, 4), (BANK4_SIZE_ADDR, 4), (VECTOR_SP, 4), (STARTUP_SP, 4),
    ):
        offset = address - 0x0800C000
        if stock[offset:offset + length] != base[offset:offset + length]:
            raise SystemExit(f"SuperFreaker already differs at 0x{address:08X}")
    patched = bytes(apply_mode(base, code))
    for start, end in changed_spans(base, patched):
        if not placement_ok(start, end):
            raise SystemExit(f"patch overlaps SuperFreaker at 0x{start:08X}")
    return base, patched


def _voices(log_text: str) -> list[int]:
    notes = []
    for line in log_text.splitlines():
        marker = "ORCHID-VOICE "
        if marker not in line:
            continue
        word = int(line.rsplit(marker, 1)[1].split()[0], 10)
        notes.append(word)
    return notes


def _notes(words: list[int]) -> list[tuple[str, int]]:
    out = []
    for word in words:
        kind = "off" if (word & 0xF0) == 0x80 else "on"
        out.append((kind, (word >> 8) & 0xFF))
    return out


def _expect(label: str, words: list[int], events: list[tuple[str, int]]) -> bool:
    got = _notes(words)
    ok = got == events
    print(f"{label}: got {got}  engine {events}  {'PASS' if ok else 'FAIL'}")
    return ok


def boot_and_compare(patched: bytes) -> int:
    import mfemu.boot as boot
    import mfemu.mfrender as mfrender
    from mfemu.midilink import EmulatedSynth

    work = Path(os.environ.get("TMPDIR", os.environ.get("TEMP", "."))) / "mfemu-orchid"
    work.mkdir(parents=True, exist_ok=True)
    raw = work / "orchid-triad.raw"
    raw.write_bytes(patched)
    flash = mfrender.build_image({}, None, str(work), quiet=True)
    hook = (
        'cpu AddHook 0x08048524 '
        '"msg=int(self.GetRegister(1).RawValue); kind=msg & 240; '
        "self.Log(LogLevel.Error, 'ORCHID-VOICE %d' % msg) "
        'if kind==128 or kind==144 else 0"'
    )
    with EmulatedSynth(firmware=str(raw), flash=flash, port=3700) as synth:
        deadline = time.time() + 180
        seen = []
        while time.time() < deadline:
            seen = boot.milestones(synth.log_path)
            if boot.MILESTONES[-1] in [name for name, _count in seen]:
                break
            time.sleep(2)
        print("milestones:", ", ".join(name for name, _count in seen) or "none")
        if boot.MILESTONES[-1] not in [name for name, _count in seen]:
            print("did not reach main()")
            print("log:", synth.log_path)
            return 1
        synth.boot()
        print(synth.monitor(hook).strip() or "hook armed")
        print(synth.monitor("sysbus WriteByte 0x200007E4 0x7F").strip() or "channel omni")

        def mail(op: int, a: int = 0, b: int = 0) -> None:
            synth.monitor("sysbus WriteByte 0x2001FF00 %d" % op)
            synth.monitor("sysbus WriteByte 0x2001FF01 %d" % a)
            synth.monitor("sysbus WriteByte 0x2001FF02 %d" % b)
            synth.monitor("sysbus WriteByte 0x2001FF03 1")

        def capture(message: list[int], expect: int) -> list[int]:
            before = Path(synth.log_path).read_text(encoding="utf-8", errors="replace")
            synth.send(message)
            end = time.time() + 45
            latest: list[int] = []
            while time.time() < end:
                text = Path(synth.log_path).read_text(encoding="utf-8", errors="replace")
                latest = _voices(text[len(before):])
                if len(latest) >= expect:
                    time.sleep(0.8)
                    text = Path(synth.log_path).read_text(encoding="utf-8", errors="replace")
                    return _voices(text[len(before):])
                time.sleep(0.4)
            return latest

        def pairs(events) -> list[tuple[str, int]]:
            return [(event.kind, event.note) for event in events]

        engine = Engine()
        major = pairs(engine.root_down(ROOT_NOTE, ROOT_NOTE, VELOCITY))
        ok = _expect("major", capture([0x90, ROOT_NOTE, VELOCITY], len(major)), major)
        moved = pairs(engine.modifier_down(Key.INV_UP))
        mail(1, 9)
        ok = _expect("inversion", capture([0x80, 1, 0x40], len(moved)), moved) and ok
        released = pairs(engine.panic())
        mail(6)
        ok = _expect("panic", capture([0x80, ROOT_NOTE, 0x40], len(released)), released) and ok
        engine.modifier_down(Key.MIN)
        minor = pairs(engine.root_down(ROOT_NOTE, ROOT_NOTE, VELOCITY))
        mail(1, 1)
        ok = _expect("minor", capture([0x90, ROOT_NOTE, VELOCITY], len(minor)), minor) and ok
        seventh = pairs(engine.modifier_down(Key.MIN7))
        mail(1, 5)
        ok = _expect("minor seventh", capture([0x80, 2, 0x40], len(seventh)), seventh) and ok
        return 0 if ok else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="build the payload and stop")
    args = parser.parse_args()
    _base, patched = build()
    print(f"payload {len(patched)} bytes")
    if args.check:
        return 0
    return boot_and_compare(patched)


if __name__ == "__main__":
    raise SystemExit(main())
