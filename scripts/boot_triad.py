"""Boot the mode image and compare its notes with the Python engine.

Builds a payload from SuperFreaker, retires 21 words of speech bank 4,
and places the chord mode. Writes that payload to a temp file.
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
    BUTTON_DOWN,
    BUTTON_UP,
    HOOK_SITE,
    KEY_SITE,
    STARTUP_SP,
    VECTOR_SP,
    apply_mode,
    changed_spans,
    compile_mode,
)
from firmware.keys import ARP_ID, OCT_MOD_ID, SHIFT_ID, button_frame, key_frame  # noqa: E402
from orchid.engine import Engine  # noqa: E402
from orchid.layout import Key  # noqa: E402
from scripts.inspect_firmware import load_mff, payload  # noqa: E402

STOCK = Path(r"C:\Users\thisi\Downloads\MicroFreak_Firmware_Update_5_0_0_2084.mff")
SUPER = Path(r"C:\Users\thisi\Downloads\superfreaker_v0_1_2_5_0_0_2084.mff")
ROOT_NOTE = 60
VELOCITY = 100


def build() -> tuple[bytes, bytes]:
    code, chord_at, key_at, button_at = compile_mode()
    stock = payload(load_mff(STOCK)[2][0][1])
    base = payload(load_mff(SUPER)[2][0][1])
    for address, length in (
        (HOOK_SITE, 4), (KEY_SITE, 4), (BUTTON_DOWN, 4), (BUTTON_UP, 4),
        (BANK4_SIZE_ADDR, 4),
        (VECTOR_SP, 4), (STARTUP_SP, 4),
    ):
        offset = address - 0x0800C000
        if stock[offset:offset + length] != base[offset:offset + length]:
            raise SystemExit(f"SuperFreaker already differs at 0x{address:08X}")
    patched = bytes(apply_mode(base, code, chord_at, key_at, button_at))
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


def _screens(text: str) -> list[str]:
    """Regions rebuilt from the frame-builder register hooks."""
    pending = None
    frames = []
    for line in text.splitlines():
        if " LCD-A " in line:
            parts = line.rsplit("LCD-A ", 1)[1].split()
            if len(parts) >= 3:
                pending = [int(part, 16) for part in parts[:3]]
        elif " LCD-B " in line and pending is not None:
            parts = line.rsplit("LCD-B ", 1)[1].split()
            if len(parts) >= 2:
                frames.append([0xF7, *pending, *[int(part, 16) for part in parts[:2]]])
            pending = None
    texts: list[str] = []
    cur = None
    for frame in frames:
        kind = frame[1]
        if kind == 0x70:
            if cur:
                texts.append(cur)
            cur = ""
        elif kind == 0x72 and cur is not None:
            cur += "".join(chr(c) for c in frame[2:6] if 32 <= c < 127 or c == 10)
        elif kind == 0x71 and cur is not None:
            cur += "".join(chr(c) for c in frame[2:5] if 32 <= c < 127)
    if cur:
        texts.append(cur)
    return texts


def _expect(label: str, words: list[int], events: list[tuple[str, int]]) -> bool:
    got = _notes(words)
    ok = got == events
    print(f"{label}: got {got}  engine {events}  {'PASS' if ok else 'FAIL'}")
    return ok


def _edges(*steps: tuple[int, bool]) -> list[int]:
    data: list[int] = []
    for ident, down in steps:
        data += button_frame(ident, down)
    return data


def _range_page(shown: list[str]) -> bool:
    """The range editor draws a short value such as '2s' and a digit."""
    return any(len(item) <= 3 and (item.endswith("s") or item.isdigit()) for item in shown)


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

        def capture(message: list[int] | None, expect: int, bus: list[int] | None = None,
                    screen: list[str] | None = None) -> list[int]:
            before = Path(synth.log_path).read_text(encoding="utf-8", errors="replace")

            def finish(text: str) -> list[int]:
                if screen is not None:
                    screen[:] = _screens(text[len(before):])
                return _voices(text[len(before):])

            if bus is not None:
                for byte in bus:
                    synth.monitor("usart2 WriteChar 0x%02X" % byte)
            else:
                synth.send(message or [])
            if expect == 0:
                time.sleep(2.5)
                text = Path(synth.log_path).read_text(encoding="utf-8", errors="replace")
                return finish(text)
            end = time.time() + 45
            latest: list[int] = []
            while time.time() < end:
                text = Path(synth.log_path).read_text(encoding="utf-8", errors="replace")
                latest = _voices(text[len(before):])
                if len(latest) >= expect:
                    time.sleep(0.8)
                    text = Path(synth.log_path).read_text(encoding="utf-8", errors="replace")
                    return finish(text)
                time.sleep(0.4)
            text = Path(synth.log_path).read_text(encoding="utf-8", errors="replace")
            if screen is not None:
                screen[:] = _screens(text[len(before):])
            return latest

        def pairs(events) -> list[tuple[str, int]]:
            return [(event.kind, event.note) for event in events]

        # No button frame has been sent. A key is one stock note, so the
        # layout did not arm during startup.
        ok = _expect(
            "boot layout off",
            capture(None, 1, key_frame(12, True, VELOCITY)),
            [("on", ROOT_NOTE)],
        )
        ok = _expect(
            "boot layout off up",
            capture(None, 1, key_frame(12, False)),
            [("off", ROOT_NOTE)],
        ) and ok

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

        cleared = pairs(engine.panic())
        mail(6)
        ok = _expect("clear", capture([0x80, 3, 0x40], len(cleared)), cleared) and ok
        engine.modifier_down(Key.MIN)
        mail(1, 1)
        ok = _expect("latch arm", capture([0x80, 4, 0x40], 0), []) and ok
        engine.set_latch(True)
        mail(3, 1)
        ok = _expect("latch on", capture([0x80, 5, 0x40], 0), []) and ok
        engine.modifier_up(Key.MIN)
        mail(2, 1)
        ok = _expect("quality up", capture([0x80, 6, 0x40], 0), []) and ok
        latched = pairs(engine.root_down(ROOT_NOTE, ROOT_NOTE, VELOCITY))
        ok = _expect("latched minor", capture([0x90, ROOT_NOTE, VELOCITY], len(latched)), latched) and ok
        unlatched = pairs(engine.set_latch(False))
        mail(3, 0)
        ok = _expect("latch off", capture([0x80, 7, 0x40], len(unlatched)), unlatched) and ok

        cleared = pairs(engine.panic())
        mail(6)
        ok = _expect("clear for bass", capture([0x80, 8, 0x40], len(cleared)), cleared) and ok
        engine.modifier_down(Key.BASS)
        mail(1, 10)
        ok = _expect("bass on", capture([0x80, 9, 0x40], 0), []) and ok
        bass_root = pairs(engine.root_down(ROOT_NOTE, ROOT_NOTE, VELOCITY))
        ok = _expect("bass root", capture([0x90, ROOT_NOTE, VELOCITY], len(bass_root)), bass_root) and ok
        bass_stop = pairs(engine.root_up(ROOT_NOTE))
        ok = _expect("bass release", capture([0x80, ROOT_NOTE, 0x40], len(bass_stop)), bass_stop) and ok

        cleared = pairs(engine.panic())
        mail(6)
        ok = _expect("clear for arp", capture([0x80, 12, 0x40], len(cleared) if cleared else 0), cleared) and ok
        engine.modifier_down(Key.ARP)
        mail(1, 11)
        ok = _expect("arp on", capture([0x80, 13, 0x40], 0), []) and ok
        arp_root = pairs(engine.root_down(ROOT_NOTE, ROOT_NOTE, VELOCITY))
        ok = _expect("arp root", capture([0x90, ROOT_NOTE, VELOCITY], len(arp_root)), arp_root) and ok
        arp_step = pairs(engine.advance(120))
        mail(5, 120)
        ok = _expect("arp step", capture([0x80, 14, 0x40], len(arp_step)), arp_step) and ok

        cleared = pairs(engine.panic())
        mail(6)
        ok = _expect("clear for keys", capture([0x80, 15, 0x40], len(cleared) if cleared else 0), cleared) and ok
        for port, pin in (("gpioPortC", 4), ("gpioPortC", 9),
                          ("gpioPortC", 12), ("gpioPortD", 14)):
            synth.monitor("%s OnGPIO %d true" % (port, pin))
        keys = Engine()
        mail(7, 1)
        major_key = pairs(keys.root_down(ROOT_NOTE, ROOT_NOTE, VELOCITY))
        ok = _expect("key root", capture(None, len(major_key), key_frame(12, True, VELOCITY)), major_key) and ok
        minor_key = pairs(keys.modifier_down(Key.MIN))
        ok = _expect("key minor", capture(None, len(minor_key), key_frame(1, True)), minor_key) and ok
        key_up = pairs(keys.root_up(ROOT_NOTE))
        ok = _expect("key release", capture(None, len(key_up), key_frame(12, False)), key_up) and ok
        ok = _expect("key minor up", capture(None, 0, key_frame(1, False)), []) and ok

        def read_word(addr: int) -> int:
            return synth.monitor_read("sysbus ReadDoubleWord 0x%08X" % addr) or 0

        def read_half(addr: int) -> int:
            return synth.monitor_read("sysbus ReadWord 0x%08X" % addr) or 0

        def write_half(addr: int, value: int) -> None:
            synth.monitor("sysbus WriteByte 0x%08X %d" % (addr, value & 0xFF))
            synth.monitor("sysbus WriteByte 0x%08X %d" % (addr + 1, (value >> 8) & 0xFF))

        def octave_raw(steps: int, kind: int) -> int:
            """Storage that the parameter reader turns back into `steps`."""
            return ((steps << 15) + kind) // (kind + 1)

        # Kbd/Octave is parameter 1 of module 3. The reader at 0x0800E644
        # turns the stored half and its type byte into 0..6, with 3 at center.
        value_ptr = read_word(0x2001C8D0)
        type_ptr = read_word(0x2001C930)
        octave_cell = value_ptr + 2 if value_ptr else 0
        octave_type = (synth.monitor_read("sysbus ReadByte 0x%08X" % (type_ptr + 2)) or 0) if type_ptr else 0
        if not octave_cell or not octave_type:
            print("octave cell: missing  FAIL")
            ok = False
        else:
            center = read_half(octave_cell)
            shifted = Engine()
            write_half(octave_cell, octave_raw(4, octave_type))
            ok = _expect("octave up control", capture(None, 0, key_frame(0, True)), []) and ok
            ok = _expect("octave up control lift", capture(None, 0, key_frame(0, False)), []) and ok
            high = pairs(shifted.root_down(12, 72, VELOCITY))
            ok = _expect("octave up root", capture(None, len(high), key_frame(12, True, VELOCITY)), high) and ok
            write_half(octave_cell, center)
            high_up = pairs(shifted.root_up(12))
            ok = _expect(
                "octave release at the old pitch",
                capture(None, len(high_up), key_frame(12, False)),
                high_up,
            ) and ok
            write_half(octave_cell, octave_raw(2, octave_type))
            ok = _expect("octave down control", capture(None, 0, key_frame(0, True)), []) and ok
            ok = _expect("octave down control lift", capture(None, 0, key_frame(0, False)), []) and ok
            low = pairs(shifted.root_down(12, 48, VELOCITY))
            ok = _expect("octave down root", capture(None, len(low), key_frame(12, True, VELOCITY)), low) and ok
            low_up = pairs(shifted.root_up(12))
            ok = _expect("octave down release", capture(None, len(low_up), key_frame(12, False)), low_up) and ok
            write_half(octave_cell, center)

        cleared = pairs(keys.panic())
        mail(6)
        ok = _expect("disarm", capture([0xC0, 0], len(cleared) if cleared else 0), cleared) and ok
        ok = _expect(
            "key stock",
            capture(None, 1, key_frame(12, True, VELOCITY)),
            [("on", ROOT_NOTE)],
        ) and ok
        ok = _expect(
            "key stock up",
            capture(None, 1, key_frame(12, False)),
            [("off", ROOT_NOTE)],
        ) and ok

        shortcut = Engine()
        ok = _expect("shift alone", capture(None, 0, button_frame(SHIFT_ID, True)), []) and ok
        ok = _expect(
            "shift still stock",
            capture(None, 1, key_frame(12, True, VELOCITY)),
            [("on", ROOT_NOTE)],
        ) and ok
        ok = _expect(
            "shift stock up",
            capture(None, 1, key_frame(12, False)),
            [("off", ROOT_NOTE)],
        ) and ok
        ok = _expect("shift release", capture(None, 0, button_frame(SHIFT_ID, False)), []) and ok
        print(synth.monitor(
            'cpu AddHook 0x080226E8 '
            '"a=int(self.GetRegister(6).RawValue) & 255; '
            'b=int(self.GetRegister(4).RawValue) & 255; '
            'c=int(self.GetRegister(5).RawValue) & 255; '
            "self.Log(LogLevel.Error, 'LCD-A %02X %02X %02X' % (a, b, c))\""
        ).strip() or "lcd hook a")
        print(synth.monitor(
            'cpu AddHook 0x080226F8 '
            '"d=int(self.GetRegister(4).RawValue) & 255; '
            'e=int(self.GetRegister(1).RawValue) & 255; '
            "self.Log(LogLevel.Error, 'LCD-B %02X %02X' % (d, e))\""
        ).strip() or "lcd hook b")
        shown: list[str] = []
        ok = _expect("oct alone", capture(None, 0, button_frame(OCT_MOD_ID, True), shown), []) and ok
        if any("ORCHID" in item for item in shown):
            print(f"oct alone text: {shown}  FAIL")
            ok = False
        ok = _expect("oct release", capture(None, 0, button_frame(OCT_MOD_ID, False)), []) and ok

        ok = _expect(
            "held stock",
            capture(None, 1, key_frame(12, True, VELOCITY)),
            [("on", ROOT_NOTE)],
        ) and ok
        ok = _expect("arm shift", capture(None, 0, button_frame(SHIFT_ID, True)), []) and ok
        shown = []
        ok = _expect(
            "arm oct",
            capture(None, 1, button_frame(OCT_MOD_ID, True), shown),
            [("off", ROOT_NOTE)],
        ) and ok
        arm_text = " ".join(shown)
        print(f"arm text: {shown}  {'PASS' if 'ORCHID ON' in arm_text else 'FAIL'}")
        ok = ("ORCHID ON" in arm_text) and ok
        shown = []
        ok = _expect(
            "arm oct repeat",
            capture(None, 0, button_frame(OCT_MOD_ID, True), shown),
            [],
        ) and ok
        if any("Range" in item for item in shown):
            print(f"repeat text: {shown}  FAIL")
            ok = False
        ok = _expect("arm key lift", capture(None, 0, key_frame(12, False)), []) and ok
        armed = pairs(shortcut.root_down(ROOT_NOTE, ROOT_NOTE, VELOCITY))
        ok = _expect(
            "armed root",
            capture(None, len(armed), key_frame(12, True, VELOCITY)),
            armed,
        ) and ok
        released = pairs(shortcut.panic())
        ok = _expect("off shift", capture(None, 0, button_frame(SHIFT_ID, False)), []) and ok
        ok = _expect("off oct up", capture(None, 0, button_frame(OCT_MOD_ID, False)), []) and ok
        ok = _expect("off shift down", capture(None, 0, button_frame(SHIFT_ID, True)), []) and ok
        shown = []
        ok = _expect(
            "off oct",
            capture(None, len(released), button_frame(OCT_MOD_ID, True), shown),
            released,
        ) and ok
        off_text = " ".join(shown)
        print(f"off text: {shown}  {'PASS' if 'ORCHID OFF' in off_text else 'FAIL'}")
        ok = ("ORCHID OFF" in off_text) and ok
        ok = _expect(
            "off key lift",
            capture(None, 1, key_frame(12, False)),
            [("off", ROOT_NOTE)],
        ) and ok
        ok = _expect(
            "stock again",
            capture(None, 1, key_frame(12, True, VELOCITY)),
            [("on", ROOT_NOTE)],
        ) and ok

        def read_byte(addr: int) -> int:
            return synth.monitor_read("sysbus ReadByte 0x%08X" % addr) or 0

        # The last shortcut left Shift and Oct|Mod down, and key 12 held.
        ok = _expect(
            "tidy",
            capture(None, 1, _edges((OCT_MOD_ID, False), (SHIFT_ID, False)) + key_frame(12, False)),
            [("off", ROOT_NOTE)],
        ) and ok

        shown = []
        ok = _expect(
            "shift latch",
            capture(None, 0, _edges(
                (SHIFT_ID, True), (SHIFT_ID, False),
                (SHIFT_ID, True), (SHIFT_ID, False),
            ), shown),
            [],
        ) and ok
        lock = read_byte(0x20004450)
        flag = read_byte(0x2000456C)
        print(f"latch lock {lock} flag {flag} screen {shown}  "
              f"{'PASS' if lock == 1 and flag == 1 else 'FAIL'}")
        ok = (lock == 1 and flag == 1) and ok
        shown = []
        ok = _expect(
            "latched oct",
            capture(None, 0, button_frame(OCT_MOD_ID, True), shown),
            [],
        ) and ok
        latched_text = " ".join(shown)
        latched_ok = "ORCHID ON" in latched_text and not _range_page(shown)
        print(f"latched oct text: {shown}  {'PASS' if latched_ok else 'FAIL'}")
        ok = latched_ok and ok
        held = Engine()
        chord = pairs(held.root_down(ROOT_NOTE, ROOT_NOTE, VELOCITY))
        ok = _expect(
            "latched key",
            capture(None, len(chord), key_frame(12, True, VELOCITY)),
            chord,
        ) and ok
        lifted = pairs(held.root_up(ROOT_NOTE))
        ok = _expect(
            "latched key up",
            capture(None, len(lifted), key_frame(12, False)),
            lifted,
        ) and ok

        shown = []
        ok = _expect(
            "latch disarm",
            capture(None, 0, _edges(
                (OCT_MOD_ID, False), (SHIFT_ID, True), (SHIFT_ID, False),
                (SHIFT_ID, True), (OCT_MOD_ID, True),
            ), shown),
            [],
        ) and ok
        unlocked = read_byte(0x20004450) == 0
        print(f"latch disarm text: {shown}  "
              f"{'PASS' if 'ORCHID OFF' in ' '.join(shown) and unlocked else 'FAIL'}")
        ok = ("ORCHID OFF" in " ".join(shown)) and unlocked and ok

        shown = []
        ok = _expect(
            "arp enable",
            capture(None, 0, _edges(
                (OCT_MOD_ID, False), (SHIFT_ID, False),
                (ARP_ID, True), (ARP_ID, False),
            ), shown),
            [],
        ) and ok
        arp_on = any("Arpeggiator" in item for item in shown) and read_byte(0x2000370A) == 0
        print(f"arp enable text: {shown}  {'PASS' if arp_on else 'FAIL'}")
        ok = arp_on and ok
        shown = []
        ok = _expect(
            "arp range",
            capture(None, 0, button_frame(OCT_MOD_ID, True), shown),
            [],
        ) and ok
        range_ok = _range_page(shown) and "ORCHID ON" not in " ".join(shown)
        print(f"arp range text: {shown}  {'PASS' if range_ok else 'FAIL'}")
        ok = range_ok and ok
        shown = []
        ok = _expect(
            "arp shortcut",
            capture(None, 0, _edges(
                (OCT_MOD_ID, False), (SHIFT_ID, True), (OCT_MOD_ID, True),
            ), shown),
            [],
        ) and ok
        arp_cut = "ORCHID ON" in " ".join(shown) and not _range_page(shown)
        print(f"arp shortcut text: {shown}  {'PASS' if arp_cut else 'FAIL'}")
        ok = arp_cut and ok

        shown = []
        ok = _expect(
            "seq enable",
            capture(None, 0, _edges(
                (OCT_MOD_ID, False), (SHIFT_ID, False),
                (SHIFT_ID, True), (OCT_MOD_ID, True),
                (OCT_MOD_ID, False), (SHIFT_ID, False),
                (SHIFT_ID, True), (ARP_ID, True), (ARP_ID, False), (SHIFT_ID, False),
            ), shown),
            [],
        ) and ok
        seq_on = any("Sequencer" in item for item in shown) and read_byte(0x2000370A) == 1
        print(f"seq enable text: {shown}  {'PASS' if seq_on else 'FAIL'}")
        ok = seq_on and ok
        shown = []
        ok = _expect(
            "seq shortcut",
            capture(None, 0, _edges((SHIFT_ID, True), (OCT_MOD_ID, True)), shown),
            [],
        ) and ok
        seq_cut = (
            "ORCHID ON" in " ".join(shown)
            and not _range_page(shown)
            and read_byte(0x2000370A) == 1
        )
        print(f"seq shortcut text: {shown}  {'PASS' if seq_cut else 'FAIL'}")
        ok = seq_cut and ok
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
