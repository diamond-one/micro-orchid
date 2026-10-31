import unittest

import path_setup  # noqa: F401

from firmware.keys import (
    OCT_MOD_ID, SHIFT_ID, button_frame, key_frame, physical_index, stock_note,
)


class KeyFrameTests(unittest.TestCase):
    def test_measured_notes(self):
        self.assertEqual(stock_note(0), 48)
        self.assertEqual(stock_note(7), 55)
        self.assertEqual(stock_note(12), 60)
        self.assertEqual(stock_note(24), 72)

    def test_down_and_up_frames(self):
        down = key_frame(12, True, 100)
        up = key_frame(12, False)
        self.assertEqual(down[:7], [0xAA, 0x00, 0x05, 0x00, 12, 0x00, 100])
        self.assertEqual(down[7], sum(down[:7]) & 0xFF)
        self.assertEqual(up[:7], [0xAA, 0x00, 0x06, 0x00, 12, 0x00, 0])
        self.assertEqual(up[7], sum(up[:7]) & 0xFF)

    def test_oct_mod_frame(self):
        down = button_frame(OCT_MOD_ID, True)
        self.assertEqual(down[:7], [0xAA, 0x20, 0x01, 0x04, 0x01, 0x00, 0x00])
        self.assertEqual(down[7], sum(down[:7]) & 0xFF)
        up = button_frame(SHIFT_ID, False)
        self.assertEqual(up[2], 0x02)
        self.assertEqual(up[3:7], [0x08, 0x04, 0x00, 0x08])

    def test_octave_moves_roots_and_leaves_the_left_keys(self):
        self.assertEqual(physical_index(stock_note(0), 3), 0)
        self.assertEqual(physical_index(stock_note(12), 3), 12)
        self.assertEqual(physical_index(stock_note(0, 4), 4), 0)
        self.assertEqual(physical_index(stock_note(12, 4), 4), 12)
        self.assertEqual(stock_note(12, 4), 72)
        self.assertEqual(physical_index(stock_note(0, 2), 2), 0)
        self.assertEqual(physical_index(stock_note(12, 2), 2), 12)
        self.assertEqual(stock_note(12, 2), 48)
        self.assertEqual(stock_note(12, 0), 24)
        self.assertEqual(stock_note(12, 6), 96)

    def test_index_is_checked(self):
        with self.assertRaises(ValueError):
            key_frame(25, True)


if __name__ == "__main__":
    unittest.main()
