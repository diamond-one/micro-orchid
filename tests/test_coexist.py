import unittest

import path_setup  # noqa: F401

from firmware.boundaries import SPEECH_CODE_CAVE
from firmware.coexist import BANNER, SHIFT_LOCK, overlaps, placement_ok, reserved


class CoexistTests(unittest.TestCase):
    def test_speech_cave_does_not_collide_with_superfreaker(self):
        self.assertEqual(overlaps(*SPEECH_CODE_CAVE), [])
        self.assertTrue(placement_ok(*SPEECH_CODE_CAVE))

    def test_their_code_window_is_reserved_including_unchanged_gaps(self):
        gap = (0x0802B91C, 0x0802B924)
        self.assertEqual(overlaps(*gap), [])
        self.assertIn("superfreaker-window", reserved(*gap))
        self.assertFalse(placement_ok(*gap))

    def test_banner_and_shift_lock_are_off_limits(self):
        self.assertFalse(placement_ok(*BANNER))
        self.assertFalse(placement_ok(*SHIFT_LOCK))
        self.assertTrue(overlaps(*BANNER))

    def test_a_known_superfreaker_hook_is_rejected(self):
        self.assertTrue(overlaps(0x08047A34, 0x08047A38))
        self.assertFalse(placement_ok(0x08047A34, 0x08047A38))


if __name__ == "__main__":
    unittest.main()
