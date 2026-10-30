import unittest

import path_setup  # noqa: F401

from firmware.keys import key_frame, stock_note


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

    def test_index_is_checked(self):
        with self.assertRaises(ValueError):
            key_frame(25, True)


if __name__ == "__main__":
    unittest.main()
