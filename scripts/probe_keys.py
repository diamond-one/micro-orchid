"""Send candidate keyboard frames and record which ones become notes.

Boots stock firmware. Does not modify a download and does not write a device.
A frame is the panel bus format: sync 0xAA, six body bytes, checksum.

    python scripts/probe_keys.py
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

STOCK = Path(r"C:\Users\thisi\Downloads\MicroFreak_Firmware_Update_5_0_0_2084.mff")
BUS = 0x200005A0
DEVICE_SLOT = BUS + 0x10
KEYBOARD = 0x20004544


def frame(*body: int) -> list[int]:
    data = [0xAA] + [b & 0xFF for b in body]
    return data + [sum(data) & 0xFF]


def voices(text: str) -> list[int]:
    notes = []
    for line in text.splitlines():
        marker = "ORCHID-VOICE "
        if marker not in line:
            continue
        notes.append(int(line.rsplit(marker, 1)[1].split()[0], 10))
    return notes


def main() -> int:
    import mfemu.boot as boot
    import mfemu.mfrender as mfrender
    from mfemu.midilink import EmulatedSynth

    work = Path(os.environ.get("TMPDIR", os.environ.get("TEMP", "."))) / "mfemu-orchid"
    work.mkdir(parents=True, exist_ok=True)
    flash = mfrender.build_image({}, None, str(work), quiet=True)
    hook = (
        'cpu AddHook 0x08048524 '
        '"msg=int(self.GetRegister(1).RawValue); kind=msg & 240; '
        "self.Log(LogLevel.Error, 'ORCHID-VOICE %d' % msg) "
        'if kind==128 or kind==144 else 0"'
    )
    with EmulatedSynth(firmware=str(STOCK), flash=flash, port=3702, timeout=180) as synth:
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
            return 1
        synth.boot()
        print(synth.monitor(hook).strip() or "hook armed")
        for port, pin in (("gpioPortC", 4), ("gpioPortC", 9),
                          ("gpioPortC", 12), ("gpioPortD", 14)):
            synth.monitor("%s OnGPIO %d true" % (port, pin))
        slot = synth.monitor_read("sysbus ReadDoubleWord 0x%X" % DEVICE_SLOT)
        print("device slot", slot)

        def send(*body: int) -> list[int]:
            before = Path(synth.log_path).read_text(encoding="utf-8", errors="replace")
            for byte in frame(*body):
                synth.monitor("usart2 WriteChar 0x%02X" % byte)
            time.sleep(0.8)
            text = Path(synth.log_path).read_text(encoding="utf-8", errors="replace")
            return voices(text[len(before):])

        def show(label: str, body: tuple[int, ...]) -> list[int]:
            got = send(*body)
            print(f"{label}: {['%02X' % b for b in body]} -> {got}")
            return got

        hit = False
        for chip in (0, 1, 2, 3):
            got = show("chip %d key 0" % chip, ((chip << 4) | 0, 0x05, 0x00, 0x00, 0x00, 100))
            hit = hit or bool(got)
        print(synth.monitor("sysbus WriteDoubleWord 0x%X 0x%X" % (DEVICE_SLOT, KEYBOARD)).strip()
              or "keyboard selected")
        slot = synth.monitor_read("sysbus ReadDoubleWord 0x%X" % DEVICE_SLOT)
        print("device slot", slot)
        for chip in (0, 3):
            for key in (0, 7):
                got = show(
                    "selected chip %d key %d" % (chip, key),
                    ((chip << 4) | 0, 0x05, 0x00, key, 0x00, 100),
                )
                hit = hit or bool(got)
                if got:
                    show("key up", ((chip << 4) | 0, 0x06, 0x00, key, 0x00, 0))
        if not hit:
            got = show("sub 3 knob shape", (0x00, 0x03, 0x00, 0x00, 0x00, 100))
            hit = hit or bool(got)
        return 0 if hit else 2


if __name__ == "__main__":
    raise SystemExit(main())
