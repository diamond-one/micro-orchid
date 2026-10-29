import unittest

import path_setup  # noqa: F401

from orchid.chords import (
    QUALITY_INTERVALS,
    Ext,
    Quality,
    apply_inversion,
    chord_symbol,
    key_mode_choice,
    resolve_quality,
    spell,
)


class SpellTests(unittest.TestCase):
    def test_spec_four_voice_examples(self):
        self.assertEqual(spell(60, Quality.MAJ, Ext.MAJ7), [60, 64, 67, 71])
        self.assertEqual(spell(60, Quality.MIN, Ext.MIN7), [60, 63, 67, 70])
        self.assertEqual(spell(60, Quality.MAJ, Ext.MIN7 | Ext.NINTH), [60, 64, 70, 74])
        self.assertEqual(spell(60, Quality.MAJ, Ext.MAJ7 | Ext.NINTH), [60, 64, 71, 74])
        self.assertEqual(spell(60, Quality.MIN, Ext.MIN7 | Ext.NINTH), [60, 63, 70, 74])

    def test_c9_drops_the_fifth(self):
        notes = spell(60, Quality.MAJ, Ext.MIN7 | Ext.NINTH, voice_limit=4)
        self.assertNotIn(67, notes)
        self.assertEqual(len(notes), 4)

    def test_extended_midi_keeps_the_fifth(self):
        self.assertEqual(
            spell(60, Quality.MAJ, Ext.MIN7 | Ext.NINTH, voice_limit=None),
            [60, 64, 67, 70, 74],
        )

    def test_every_quality_and_extension_stays_in_range(self):
        extensions = [Ext(mask) for mask in range(16)]
        for root in range(48, 73):
            for quality in Quality:
                for ext in extensions:
                    limited = spell(root, quality, ext, voice_limit=4)
                    full = spell(root, quality, ext, voice_limit=None)
                    self.assertLessEqual(len(limited), 4)
                    self.assertTrue(all(0 <= note <= 127 for note in full))
                    self.assertIn(root, full)

    def test_bare_qualities_match_the_interval_model(self):
        for quality, intervals in QUALITY_INTERVALS.items():
            notes = spell(60, quality, voice_limit=None)
            self.assertEqual(notes, [60 + step for step in intervals])

    def test_twelve_roots_keep_pitch_classes(self):
        for root in range(60, 72):
            notes = spell(root, Quality.MIN, Ext.MIN7, voice_limit=None)
            self.assertEqual([(note - root) % 12 for note in notes], [0, 3, 7, 10])

    def test_upper_c(self):
        self.assertEqual(spell(72, Quality.MAJ), [72, 76, 79])

    def test_inversion_rotates_and_stops_at_the_top(self):
        self.assertEqual(apply_inversion([60, 64, 67], 1), [64, 67, 72])
        self.assertEqual(apply_inversion([60, 64, 67], -1), [55, 60, 64])
        self.assertEqual(spell(120, Quality.MAJ, inversion=1), [120, 124, 127])

    def test_sixth_moves_up_only_with_a_seventh(self):
        self.assertIn(69, spell(60, Quality.MAJ, Ext.SIXTH | Ext.MIN7, voice_limit=None))
        raised = spell(
            60, Quality.MAJ, Ext.SIXTH | Ext.MIN7, sixth_up=True, voice_limit=None
        )
        self.assertIn(81, raised)
        self.assertNotIn(69, raised)
        plain = spell(60, Quality.MAJ, Ext.SIXTH, sixth_up=True, voice_limit=None)
        self.assertIn(69, plain)

    def test_secret_qualities(self):
        self.assertEqual(resolve_quality([Quality.MAJ, Quality.SUS]), Quality.AUG)
        self.assertEqual(resolve_quality([Quality.MIN, Quality.SUS]), Quality.MIN4)
        self.assertEqual(resolve_quality([Quality.DIM, Quality.SUS]), Quality.POW)
        self.assertEqual(resolve_quality([Quality.MIN, Quality.MAJ]), Quality.MAJ)
        self.assertEqual(resolve_quality([]), Quality.MAJ)

    def test_key_mode_c_sharp_in_c_is_c_suspended(self):
        quality, shift = key_mode_choice("major", 1, 0)
        self.assertEqual(quality, Quality.SUS)
        self.assertEqual(shift, -1)

    def test_symbols_for_the_spec_chords(self):
        self.assertEqual(chord_symbol(60, Quality.MAJ), "C")
        self.assertEqual(chord_symbol(60, Quality.MAJ, Ext.MAJ7), "Cmaj7")
        self.assertEqual(chord_symbol(60, Quality.MIN, Ext.MIN7), "Cm7")
        self.assertEqual(chord_symbol(60, Quality.MAJ, Ext.MIN7 | Ext.NINTH), "C9")
        self.assertEqual(chord_symbol(60, Quality.MAJ, Ext.MAJ7 | Ext.NINTH), "Cmaj9")
        self.assertEqual(chord_symbol(60, Quality.MIN, Ext.MIN7 | Ext.NINTH), "Cm9")


if __name__ == "__main__":
    unittest.main()
