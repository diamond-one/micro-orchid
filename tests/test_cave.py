import struct
import unittest

import path_setup  # noqa: F401

from firmware.cave import gaps, thumb_literal_address
from firmware.speech import REGION_END, TABLE, banks


def word(value: int) -> bytes:
    return struct.pack("<I", value)


class CaveTests(unittest.TestCase):
    def test_thumb_literal_uses_the_aligned_pc(self):
        # ldr r0, [pc, #0x18c] at the documented speech load.
        self.assertEqual(thumb_literal_address(0x0805ECCA, 0x18C), 0x0805EE58)

    def test_bytes_between_two_handlers_are_a_gap(self):
        base = 0x08000000
        image = bytearray(0x20)
        image[0:4] = word(0x20001000)
        image[4:8] = word(base + 0x11)       # bx lr at 0x10
        image[8:12] = word(base + 0x19)      # bx lr at 0x18
        image[12:16] = word(0xFFFFFFFF)      # end of the vector table
        image[0x10:0x12] = b"\x70\x47"       # bx lr
        image[0x12:0x18] = b"\xff" * 6
        image[0x18:0x1A] = b"\x70\x47"
        found = {(gap.start, gap.end) for gap in gaps(bytes(image), base)}
        self.assertIn((base + 0x12, base + 0x18), found)

    def test_a_loaded_object_is_not_a_gap(self):
        base = 0x08000000
        image = bytearray(0x30)
        image[0:4] = word(0x20001000)
        image[4:8] = word(base + 0x0D)       # ldr at 0x0C
        image[8:12] = word(0xFFFFFFFF)
        # ldr r0, [pc, #0] ; pool at align(0x0C+4)+0 = 0x10
        image[0x0C:0x0E] = b"\x00\x48"
        image[0x0E:0x10] = b"\x70\x47"       # bx lr
        image[0x10:0x14] = word(base + 0x20)
        image[0x14:0x20] = b"\xff" * 12
        image[0x20:0x28] = b"\xa5" * 8
        found = gaps(bytes(image), base)
        self.assertIn((base + 0x14, base + 0x20), [(gap.start, gap.end) for gap in found])
        for gap in found:
            self.assertFalse(gap.start <= base + 0x20 < gap.end)

    def test_speech_descriptor_is_five_pointer_size_pairs(self):
        base = 0x08000000
        image = bytearray(TABLE - base + 40)
        pairs = (
            (0x08078860, 0x4D1),
            (0x08078D34, 0x384),
            (0x080790B8, 0x610),
            (0x080796C8, 0x9DC),
            (0x0807A0A4, 0x12C2),
        )
        for index, (pointer, size) in enumerate(pairs):
            struct.pack_into("<II", image, TABLE - base + 8 * index, pointer, size)
        self.assertEqual(banks(bytes(image), base), list(pairs))
        self.assertEqual(REGION_END, 0x0807B367)


if __name__ == "__main__":
    unittest.main()
