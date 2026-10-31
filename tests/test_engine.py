import unittest

import path_setup  # noqa: F401

from orchid.engine import Engine
from orchid.layout import Key


def ons(events):
    return [event.note for event in events if event.kind == "on"]


def offs(events):
    return [event.note for event in events if event.kind == "off"]


class EngineTests(unittest.TestCase):
    def test_root_alone_is_a_major_triad(self):
        engine = Engine()
        events = engine.root_down(12, 60)
        self.assertEqual(ons(events), [60, 64, 67])
        self.assertEqual(engine.held_notes(), (60, 64, 67))

    def test_modifier_before_root_and_root_before_modifier(self):
        first = Engine()
        first.modifier_down(Key.MIN)
        self.assertEqual(ons(first.root_down(12, 60)), [60, 63, 67])

        second = Engine()
        second.root_down(12, 60)
        change = second.modifier_down(Key.MIN)
        self.assertEqual(offs(change), [64])
        self.assertEqual(ons(change), [63])
        self.assertEqual(second.held_notes(), (60, 63, 67))

    def test_extension_while_a_root_is_held(self):
        engine = Engine()
        engine.root_down(12, 60)
        change = engine.modifier_down(Key.MIN7)
        self.assertEqual(ons(change), [70])
        self.assertEqual(offs(change), [])
        self.assertEqual(engine.held_notes(), (60, 64, 67, 70))
        minor = engine.modifier_down(Key.MIN)
        self.assertIn(64, offs(minor))
        self.assertIn(63, ons(minor))
        self.assertEqual(engine.held_notes(), (60, 63, 67, 70))

    def test_release_matches_every_note_on(self):
        engine = Engine()
        engine.modifier_down(Key.MIN)
        engine.modifier_down(Key.NINTH)
        played = ons(engine.root_down(12, 60))
        released = offs(engine.root_up(12))
        self.assertEqual(sorted(released), sorted(played))
        self.assertEqual(engine.held_notes(), ())

    def test_latch_holds_the_quality_after_the_key_comes_up(self):
        engine = Engine()
        engine.modifier_down(Key.MIN)
        engine.set_latch(True)
        engine.modifier_up(Key.MIN)
        engine.root_down(12, 60)
        self.assertEqual(engine.held_notes(), (60, 63, 67))
        engine.set_latch(False)
        self.assertEqual(engine.held_notes(), (60, 64, 67))

    def test_shared_pitches_stay_until_the_last_root_releases(self):
        engine = Engine(voice_limit=None)
        engine.root_down(1, 60)  # C major
        engine.root_down(2, 67)  # G major shares G
        self.assertEqual(engine.held_notes(), (60, 64, 67, 71, 74))
        gone = engine.root_up(1)
        self.assertEqual(offs(gone), [60, 64])
        self.assertEqual(engine.held_notes(), (67, 71, 74))
        engine.root_up(2)
        self.assertEqual(engine.held_notes(), ())

    def test_two_roots_share_four_voices(self):
        engine = Engine(voice_limit=4)
        engine.root_down(12, 60)
        engine.root_down(19, 67)
        self.assertEqual(len(engine.held_notes()), 4)
        self.assertLessEqual(len(engine.held_notes()), 4)

    def test_bass_adds_the_lowest_voiced_note_an_octave_down(self):
        engine = Engine()
        engine.modifier_down(Key.BASS)
        self.assertEqual(ons(engine.root_down(12, 60)), [48, 60, 64, 67])
        self.assertEqual(sorted(offs(engine.root_up(12))), [48, 60, 64, 67])
        engine.root_down(12, 60)
        engine.modifier_down(Key.INV_UP)
        self.assertEqual(engine.held_notes(), (52, 64, 67, 72))
        engine.modifier_down(Key.BASS)
        self.assertEqual(engine.held_notes(), (64, 67, 72))
        seventh = Engine()
        seventh.modifier_down(Key.MIN)
        seventh.modifier_down(Key.MIN7)
        seventh.modifier_down(Key.BASS)
        seventh.root_down(12, 60)
        self.assertEqual(seventh.held_notes(), (48, 60, 63, 70))

    def test_arp_sounds_one_note_at_a_time(self):
        engine = Engine(arp_ms=100)
        engine.modifier_down(Key.ARP)
        self.assertEqual(ons(engine.root_down(12, 60)), [60])
        step = engine.advance(100)
        self.assertEqual(offs(step), [60])
        self.assertEqual(ons(step), [64])

    def test_inversion_moves_a_held_chord(self):
        engine = Engine()
        engine.root_down(12, 60)
        moved = engine.modifier_down(Key.INV_UP)
        self.assertIn(60, offs(moved))
        self.assertIn(72, ons(moved))
        self.assertEqual(engine.held_notes(), (64, 67, 72))

    def test_key_mode_can_be_overridden_by_a_held_quality(self):
        engine = Engine()
        engine.set_key_mode("major", tonic=0)
        engine.root_down(13, 61)
        self.assertEqual(engine.held_notes(), (60, 65, 67))
        engine.modifier_down(Key.MAJ)
        self.assertEqual(engine.held_notes(), (61, 65, 68))

    def test_panic_clears_a_held_chord(self):
        engine = Engine()
        engine.root_down(12, 60)
        engine.modifier_down(Key.MIN)
        gone = engine.panic()
        self.assertEqual(sorted(offs(gone)), [60, 63, 67])
        self.assertEqual(engine.held_notes(), ())
        self.assertFalse(engine.latch)


if __name__ == "__main__":
    unittest.main()
