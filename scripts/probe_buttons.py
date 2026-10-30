"""Press panel ids and print the display text they produce.

Stock firmware. No device write. Display bytes are logged by an emulator
hook because Renode locks the USART2 capture file on Windows.
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

STOCK = Path(r"C:\Users\thisi\Downloads\MicroFreak_Firmware_Update_5_0_0_2084.mff")
IDS = [
    0x400, 0x401, 0x402, 0x403, 0x404, 0x405, 0x406, 0x407,
    0x408, 0x409, 0x40A, 0x40B, 0x40C, 0x40D, 0x40E, 0x40F,
    0x502, 0x503, 0x700, 0x902, 0x904, 0x1100,
]


def frame(*body: int) -> list[int]:
    data = [0xAA] + [b & 0xFF for b in body]
    return data + [sum(data) & 0xFF]


def voices(text: str) -> list[str]:
    out = []
    for line in text.splitlines():
        marker = "ORCHID-VOICE "
        if marker not in line:
            continue
        word = int(line.rsplit(marker, 1)[1].split()[0], 10)
        kind = "off" if (word & 0xF0) == 0x80 else "on"
        out.append(f"{kind} {(word >> 8) & 0xFF}")
    return out


def lcd(text: str) -> str:
    chars = []
    for line in text.splitlines():
        marker = "LCD "
        if marker not in line:
            continue
        parts = line.rsplit(marker, 1)[1].split()
        kind = int(parts[0], 16)
        word = int(parts[1], 16)
        raw = bytes((word & 0xFF, (word >> 8) & 0xFF,
                     (word >> 16) & 0xFF, (word >> 24) & 0xFF))
        kind = raw[0]
        word_chars = raw[1:]
        if kind == 0x70:
            chars.append(" | ")
        elif kind in (0x71, 0x72):
            chars.append("".join(chr(c) if 32 <= c < 127 else "" for c in word_chars))
    return "".join(chars).strip()


def main() -> int:
    import mfemu.boot as boot
    import mfemu.mfrender as mfrender
    from mfemu.frontpanel import frame as bus_frame
    from mfemu.midilink import EmulatedSynth

    work = Path(os.environ.get("TMPDIR", os.environ.get("TEMP", "."))) / "mfemu-orchid"
    work.mkdir(parents=True, exist_ok=True)
    flash = mfrender.build_image({}, None, str(work), quiet=True)
    with EmulatedSynth(firmware=str(STOCK), flash=flash, port=3703, timeout=180) as synth:
        deadline = time.time() + 180
        seen = []
        while time.time() < deadline:
            seen = boot.milestones(synth.log_path)
            if boot.MILESTONES[-1] in [name for name, _count in seen]:
                break
            time.sleep(2)
        if boot.MILESTONES[-1] not in [name for name, _count in seen]:
            print("did not reach main()")
            return 1
        synth.boot()
        synth.monitor(
            'cpu AddHook 0x08048524 '
            '"msg=int(self.GetRegister(1).RawValue); kind=msg & 240; '
            "self.Log(LogLevel.Error, 'ORCHID-VOICE %d' % msg) "
            'if kind==128 or kind==144 else 0"'
        )
        synth.monitor(
            'cpu AddHook 0x080226DE '
            '"b0=int(self.GetRegister(3).RawValue) & 255; '
            'w=int(self.GetRegister(4).RawValue); '
            "self.Log(LogLevel.Error, 'LCD %02X %08X' % (b0, w)) if b0==247 else 0\""
        )
        for port, pin in (("gpioPortC", 4), ("gpioPortC", 9),
                          ("gpioPortC", 12), ("gpioPortD", 14)):
            synth.monitor("%s OnGPIO %d true" % (port, pin))

        def since(mark: str) -> str:
            text = Path(synth.log_path).read_text(encoding="utf-8", errors="replace")
            return text[len(mark):]

        def key(index: int, down: bool) -> None:
            mark = Path(synth.log_path).read_text(encoding="utf-8", errors="replace")
            body = (0x00, 0x05 if down else 0x06, 0x00, index, 0x00, 100 if down else 0)
            for byte in frame(*body):
                synth.monitor("usart2 WriteChar 0x%02X" % byte)
            time.sleep(0.4)
            print(f"key {index} {'down' if down else 'up'}: {voices(since(mark))}")

        def press(ident: int) -> None:
            mark = Path(synth.log_path).read_text(encoding="utf-8", errors="replace")
            for body in (
                (0x20, 0x01, ident >> 8, ident & 0xFF, 0x00, 0x00),
                (0x20, 0x02, ident >> 8, ident & 0xFF, 0x08, 0x00),
            ):
                for byte in bus_frame(*body):
                    synth.monitor("usart2 WriteChar 0x%02X" % byte)
                time.sleep(0.2)
            time.sleep(0.5)
            print(f"press {ident:04X}: {lcd(since(mark))}")

        key(12, True)
        key(12, False)
        for ident in (0x0803, *IDS):
            press(ident)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
