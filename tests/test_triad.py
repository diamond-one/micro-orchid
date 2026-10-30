import struct
import unittest

import path_setup  # noqa: F401

from firmware.boundaries import APPLICATION, PATCH_MANIFEST
from firmware.coexist import placement_ok
from firmware.triad import (
    BANK4_SIZE,
    BANK4_SIZE_ADDR,
    BANK4_SIZE_AFTER,
    BASE,
    CAVE,
    CAVE_END,
    DISPATCH,
    HOOK_SITE,
    apply_triad,
    compile_hook,
    encode_bl,
    expand_message,
    triad_notes,
)
from orchid.chords import Quality, spell


def _image() -> bytearray:
    image = bytearray(473695)
    image[HOOK_SITE - BASE:HOOK_SITE - BASE + 4] = encode_bl(HOOK_SITE, DISPATCH)
    struct.pack_into("<I", image, BANK4_SIZE_ADDR - BASE, BANK4_SIZE)
    return image


class TriadTests(unittest.TestCase):
    def test_bl_matches_the_compiled_call(self):
        # The hook's own bl to midi_dispatch, read back from the object file.
        self.assertEqual(encode_bl(0x0807B2AE, DISPATCH).hex(), "cdf739f9")

    def test_major_triad_matches_the_python_engine(self):
        self.assertEqual(triad_notes(60), spell(60, Quality.MAJ))
        self.assertEqual(triad_notes(125), [125])
        self.assertEqual(triad_notes(127), [127])

    def test_only_note_messages_grow_a_chord(self):
        note_on = 0x90 | (60 << 8) | (100 << 16)
        expanded = expand_message(note_on)
        self.assertEqual([(word >> 8) & 0xFF for word in expanded], [60, 64, 67])
        self.assertEqual(expand_message(0xC0 | (3 << 8)), [0xC0 | (3 << 8)])

    def test_hook_fits_and_returns_to_midi_dispatch(self):
        from capstone import CS_ARCH_ARM, CS_MODE_THUMB, Cs

        code = compile_hook()
        self.assertLessEqual(len(code), CAVE_END - CAVE)
        md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
        calls = [
            ins.op_str
            for ins in md.disasm(code, CAVE)
            if ins.mnemonic in ("bl", "b.w")
        ]
        self.assertTrue(any(call.endswith("8048524") for call in calls), calls)

    def test_patch_touches_only_the_three_accepted_ranges(self):
        code = compile_hook()
        image = bytes(_image())
        patched = apply_triad(image, code)
        self.assertEqual(struct.unpack_from("<I", patched, BANK4_SIZE_ADDR - BASE)[0], BANK4_SIZE_AFTER)
        self.assertEqual(patched[CAVE - BASE:CAVE - BASE + len(code)], code)
        for start, end in (
            (HOOK_SITE, HOOK_SITE + 4),
            (BANK4_SIZE_ADDR, BANK4_SIZE_ADDR + 4),
            (CAVE, CAVE + len(code)),
        ):
            self.assertTrue(placement_ok(start, end), hex(start))
            self.assertTrue(APPLICATION[0] <= start and end <= APPLICATION[1])
        self.assertEqual(
            [(item["start"], item["end"]) for item in PATCH_MANIFEST],
            [
                (HOOK_SITE, HOOK_SITE + 4),
                (BANK4_SIZE_ADDR, BANK4_SIZE_ADDR + 4),
                (CAVE, CAVE + len(code)),
            ],
        )


if __name__ == "__main__":
    unittest.main()
