"""The C engine matches the Python engine on the cases the firmware must play."""

import ctypes
import subprocess
import unittest
from pathlib import Path

import path_setup  # noqa: F401

from orchid.layout import Key

ROOT = Path(__file__).resolve().parents[1]
DLL = ROOT / ".tools" / "orchid_engine.dll"
CLANG = Path(r"C:\Program Files\LLVM\bin\clang.exe")

KEYS = {
    Key.DIM: 0, Key.MIN: 1, Key.MAJ: 2, Key.SUS: 3,
    Key.SIXTH: 4, Key.MIN7: 5, Key.MAJ7: 6, Key.NINTH: 7,
    Key.INV_DOWN: 8, Key.INV_UP: 9, Key.STRUM: 10, Key.ARP: 11,
}


class Event(ctypes.Structure):
    _fields_ = [("kind", ctypes.c_uint8), ("note", ctypes.c_uint8), ("velocity", ctypes.c_uint8)]


def library():
    DLL.parent.mkdir(exist_ok=True)
    source = ROOT / "firmware" / "orchid_engine.c"
    if not DLL.exists() or DLL.stat().st_mtime < source.stat().st_mtime:
        result = subprocess.run(
            [str(CLANG), "-shared", "-O2", "-DORCHID_EXPORT", "-o", str(DLL), str(source)],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr)
    lib = ctypes.CDLL(str(DLL))
    lib.orchid_reset.restype = None
    lib.orchid_set_voice_limit.argtypes = [ctypes.c_int]
    lib.orchid_set_timing.argtypes = [ctypes.c_int, ctypes.c_int]
    for name in (
        "orchid_modifier", "orchid_root", "orchid_latch", "orchid_key_mode",
        "orchid_advance", "orchid_panic",
    ):
        getattr(lib, name).restype = ctypes.c_int
    lib.orchid_held.restype = ctypes.c_int
    lib.orchid_pending_count.restype = ctypes.c_int
    return lib


class FwEngine:
    def __init__(self, voice_limit=4, strum_ms=30, arp_ms=120):
        self.lib = library()
        self.lib.orchid_reset()
        self.lib.orchid_set_voice_limit(0 if voice_limit is None else voice_limit)
        self.lib.orchid_set_timing(strum_ms, arp_ms)
        self._buf = (Event * 32)()

    def _take(self, count):
        return [(self._buf[i].kind, self._buf[i].note) for i in range(min(count, 32))]

    def modifier(self, key, down=True):
        count = self.lib.orchid_modifier(KEYS[key], int(down), self._buf, 32)
        return self._take(count)

    def root(self, key, note, velocity=100, on=True):
        count = self.lib.orchid_root(key, note, velocity, int(on), self._buf, 32)
        return self._take(count)

    def latch(self, enabled):
        count = self.lib.orchid_latch(int(enabled), self._buf, 32)
        return self._take(count)

    def key_mode(self, mode, tonic=0):
        number = 0 if mode is None else (1 if mode == "major" else 2)
        count = self.lib.orchid_key_mode(number, tonic, self._buf, 32)
        return self._take(count)

    def advance(self, ms):
        count = self.lib.orchid_advance(ms, self._buf, 32)
        return self._take(count)

    def panic(self):
        count = self.lib.orchid_panic(self._buf, 32)
        return self._take(count)

    def held(self):
        raw = (ctypes.c_uint8 * 16)()
        count = self.lib.orchid_held(raw, 16)
        return tuple(raw[i] for i in range(count))

    def pending(self):
        return self.lib.orchid_pending_count()


def ons(events):
    return [note for kind, note in events if kind == 1]


def offs(events):
    return [note for kind, note in events if kind == 0]


class FirmwareEngineTests(unittest.TestCase):
    def test_root_alone_is_a_major_triad(self):
        engine = FwEngine()
        self.assertEqual(ons(engine.root(12, 60)), [60, 64, 67])
        self.assertEqual(engine.held(), (60, 64, 67))

    def test_minor_before_and_after_the_root(self):
        first = FwEngine()
        first.modifier(Key.MIN)
        self.assertEqual(ons(first.root(12, 60)), [60, 63, 67])
        second = FwEngine()
        second.root(12, 60)
        change = second.modifier(Key.MIN)
        self.assertEqual(offs(change), [64])
        self.assertEqual(ons(change), [63])
        self.assertEqual(second.held(), (60, 63, 67))

    def test_seventh_while_held_then_minor(self):
        engine = FwEngine()
        engine.root(12, 60)
        change = engine.modifier(Key.MIN7)
        self.assertEqual(ons(change), [70])
        self.assertEqual(engine.held(), (60, 64, 67, 70))
        minor = engine.modifier(Key.MIN)
        self.assertIn(64, offs(minor))
        self.assertIn(63, ons(minor))
        self.assertEqual(engine.held(), (60, 63, 67, 70))

    def test_release_matches_the_notes_that_sounded(self):
        engine = FwEngine()
        engine.modifier(Key.MIN)
        engine.modifier(Key.NINTH)
        played = ons(engine.root(12, 60))
        self.assertEqual(sorted(offs(engine.root(12, 60, on=False))), sorted(played))
        self.assertEqual(engine.held(), ())

    def test_latch_keeps_minor_after_the_key_lifts(self):
        engine = FwEngine()
        engine.modifier(Key.MIN)
        engine.latch(True)
        engine.modifier(Key.MIN, down=False)
        engine.root(12, 60)
        self.assertEqual(engine.held(), (60, 63, 67))
        engine.latch(False)
        self.assertEqual(engine.held(), (60, 64, 67))

    def test_shared_pitch_stays_until_the_last_root(self):
        engine = FwEngine(voice_limit=None)
        engine.root(1, 60)
        engine.root(2, 67)
        self.assertEqual(engine.held(), (60, 64, 67, 71, 74))
        self.assertEqual(offs(engine.root(1, 60, on=False)), [60, 64])
        self.assertEqual(engine.held(), (67, 71, 74))

    def test_two_roots_share_four_voices(self):
        engine = FwEngine()
        engine.root(12, 60)
        engine.root(19, 67)
        self.assertLessEqual(len(engine.held()), 4)
        self.assertGreater(len(engine.held()), 0)

    def test_strum_and_a_release_cancels_what_has_not_sounded(self):
        engine = FwEngine(strum_ms=30)
        engine.modifier(Key.STRUM)
        self.assertEqual(ons(engine.root(12, 60)), [60])
        self.assertEqual(engine.pending(), 2)
        self.assertEqual(ons(engine.advance(30)), [64])
        engine.root(12, 60, on=False)
        self.assertEqual(engine.pending(), 0)
        self.assertEqual(engine.held(), ())

    def test_arp_plays_one_note(self):
        engine = FwEngine(arp_ms=100)
        engine.modifier(Key.ARP)
        self.assertEqual(ons(engine.root(12, 60)), [60])
        step = engine.advance(100)
        self.assertEqual(offs(step), [60])
        self.assertEqual(ons(step), [64])

    def test_inversion_raises_the_root(self):
        engine = FwEngine()
        engine.root(12, 60)
        moved = engine.modifier(Key.INV_UP)
        self.assertIn(60, offs(moved))
        self.assertIn(72, ons(moved))
        self.assertEqual(engine.held(), (64, 67, 72))

    def test_key_mode_yields_to_a_held_quality(self):
        engine = FwEngine()
        engine.key_mode("major", 0)
        engine.root(13, 61)
        self.assertEqual(engine.held(), (60, 65, 67))
        engine.modifier(Key.MAJ)
        self.assertEqual(engine.held(), (61, 65, 68))

    def test_panic_releases_and_clears(self):
        engine = FwEngine()
        engine.root(12, 60)
        engine.modifier(Key.MIN)
        self.assertEqual(sorted(offs(engine.panic())), [60, 63, 67])
        self.assertEqual(engine.held(), ())


if __name__ == "__main__":
    unittest.main()
