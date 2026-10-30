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
    BUTTON_DOWN,
    BUTTON_FN,
    BUTTON_UP,
    HOOK_SITE,
    KEY_SITE,
    MODE_CAVE,
    OLD_STACK,
    STARTUP_SP,
    VECTOR_SP,
    apply_mode,
    apply_triad,
    compile_hook,
    compile_mode,
    encode_bl,
    expand_message,
    triad_notes,
)
from orchid.chords import Quality, spell


def _image() -> bytearray:
    image = bytearray(473695)
    image[HOOK_SITE - BASE:HOOK_SITE - BASE + 4] = encode_bl(HOOK_SITE, DISPATCH)
    image[KEY_SITE - BASE:KEY_SITE - BASE + 4] = encode_bl(KEY_SITE, DISPATCH)
    image[BUTTON_DOWN - BASE:BUTTON_DOWN - BASE + 4] = encode_bl(BUTTON_DOWN, BUTTON_FN)
    image[BUTTON_UP - BASE:BUTTON_UP - BASE + 4] = encode_bl(BUTTON_UP, BUTTON_FN)
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

    def test_mode_fits_in_twenty_one_retired_words(self):
        code, chord_at, key_at, button_at = compile_mode()
        image = bytearray(_image())
        struct.pack_into("<I", image, VECTOR_SP - BASE, OLD_STACK)
        struct.pack_into("<I", image, STARTUP_SP - BASE, OLD_STACK)
        patched = apply_mode(bytes(image), code, chord_at, key_at, button_at)
        self.assertEqual(
            [(item["start"], item["end"]) for item in PATCH_MANIFEST],
            [
                (VECTOR_SP, VECTOR_SP + 4),
                (HOOK_SITE, HOOK_SITE + 4),
                (KEY_SITE, KEY_SITE + 4),
                (BUTTON_DOWN, BUTTON_DOWN + 4),
                (BUTTON_UP, BUTTON_UP + 4),
                (STARTUP_SP, STARTUP_SP + 4),
                (BANK4_SIZE_ADDR, BANK4_SIZE_ADDR + 4),
                (MODE_CAVE, MODE_CAVE + len(code)),
            ],
        )
        for item in PATCH_MANIFEST:
            self.assertTrue(placement_ok(int(item["start"]), int(item["end"])))
        self.assertEqual(
            patched[HOOK_SITE - BASE:HOOK_SITE - BASE + 4],
            encode_bl(HOOK_SITE, MODE_CAVE + chord_at),
        )
        self.assertEqual(
            patched[KEY_SITE - BASE:KEY_SITE - BASE + 4],
            encode_bl(KEY_SITE, MODE_CAVE + key_at),
        )
        for site in (BUTTON_DOWN, BUTTON_UP):
            self.assertEqual(
                patched[site - BASE:site - BASE + 4],
                encode_bl(site, MODE_CAVE + button_at),
            )


if __name__ == "__main__":
    unittest.main()
