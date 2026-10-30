import unittest

import path_setup  # noqa: F401

from firmware.boundaries import (
    APPLICATION,
    BOOTLOADER,
    FACTORY_DATA,
    PATCH_MANIFEST,
    SPEECH_CODE_CAVE,
    STOCK_PAYLOAD_SHA256,
    cave_size,
    protected,
)


class SafetyTests(unittest.TestCase):
    def test_patch_manifest_stays_inside_the_application(self):
        self.assertEqual(len(PATCH_MANIFEST), 8)
        for item in PATCH_MANIFEST:
            start, end = int(item["start"]), int(item["end"])
            self.assertGreater(end, start)
            self.assertFalse(protected(start))
            self.assertTrue(APPLICATION[0] <= start and end <= APPLICATION[1])

    def test_bootloader_and_factory_data_are_protected(self):
        self.assertTrue(protected(BOOTLOADER[0]))
        self.assertTrue(protected(FACTORY_DATA[0]))
        self.assertFalse(protected(APPLICATION[0]))

    def test_documented_cave_is_too_small_for_this_engine(self):
        self.assertLess(cave_size(), 512)
        self.assertEqual(SPEECH_CODE_CAVE[0], 0x0807B264)

    def test_stock_hash_is_the_tools_payload_digest(self):
        self.assertEqual(len(STOCK_PAYLOAD_SHA256), 64)


if __name__ == "__main__":
    unittest.main()