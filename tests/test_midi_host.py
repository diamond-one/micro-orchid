import unittest

import path_setup  # noqa: F401

from orchid.layout import MODIFIER_COUNT
from orchid.midi_host import Host


def ons(events):
    return [event.note for event in events if event.kind == "on"]


def offs(events):
    return [event.note for event in events if event.kind == "off"]


def play(host, index, kind="on", velocity=100):
    return host.note(kind, host.input_base + index, velocity)


class HostTests(unittest.TestCase):
    def test_power_on_is_normal_mode(self):
        host = Host()
        result = host.power_on()
        self.assertFalse(result.enabled)
        self.assertFalse(host.enabled)

    def test_shift_or_oct_mod_alone_does_not_enable(self):
        host = Host()
        shift = host.button("shift", True)
        self.assertFalse(shift.enabled)
        self.assertEqual(shift.stock_button, "shift")
        host.button("shift", False)
        oct_mod = host.button("oct_mod", True)
        self.assertFalse(oct_mod.enabled)
        self.assertEqual(oct_mod.stock_button, "oct_mod")

    def test_shortcut_toggles_once_per_press(self):
        host = Host()
        host.button("shift", True)
        armed = host.button("oct_mod", True)
        self.assertTrue(armed.enabled)
        self.assertEqual(armed.display, "ORCHID ON")
        again = host.button("oct_mod", True)
        self.assertTrue(again.enabled)
        self.assertIsNone(again.display)
        host.button("oct_mod", False)
        host.button("shift", False)
        host.button("shift", True)
        off = host.button("oct_mod", True)
        self.assertFalse(off.enabled)
        self.assertEqual(off.display, "ORCHID OFF")

    def test_held_shortcut_at_power_on_does_not_enable(self):
        host = Host()
        result = host.power_on(shift=True, oct_mod=True)
        self.assertFalse(result.enabled)
        self.assertFalse(host.button("shift", True).enabled)

    def test_disabled_notes_pass_through_and_enabling_releases_them(self):
        host = Host()
        thru = play(host, 12)
        self.assertEqual(ons(thru.events), [host.input_base + 12])
        self.assertEqual(thru.events[0].channel, host.output_channel)
        host.button("shift", True)
        enabled = host.button("oct_mod", True)
        self.assertEqual(offs(enabled.events), [host.input_base + 12])
        self.assertTrue(enabled.enabled)

    def test_one_root_plays_a_chord_and_leaving_mode_releases_it(self):
        host = Host()
        host.button("shift", True)
        host.button("oct_mod", True)
        host.button("oct_mod", False)
        host.button("shift", False)
        chord = play(host, MODIFIER_COUNT)
        self.assertEqual(ons(chord.events), [60, 64, 67])
        host.button("shift", True)
        off = host.button("oct_mod", True)
        self.assertEqual(sorted(offs(off.events)), [60, 64, 67])
        self.assertEqual(host.engine.held_notes(), ())
        self.assertEqual(off.display, "ORCHID OFF")

    def test_left_key_changes_the_held_root(self):
        host = Host()
        host.button("shift", True)
        host.button("oct_mod", True)
        play(host, MODIFIER_COUNT)
        minor = play(host, 1)  # minor modifier
        self.assertEqual(host.engine.held_notes(), (60, 63, 67))
        self.assertTrue(minor.enabled)

    def test_output_channel_is_not_treated_as_playing(self):
        host = Host()
        host.button("shift", True)
        host.button("oct_mod", True)
        echo = host.note("on", 60, channel=host.output_channel)
        self.assertEqual(echo.events, [])
        self.assertEqual(host.engine.held_notes(), ())

    def test_repeated_toggles_do_not_stick_notes(self):
        host = Host()
        for _ in range(4):
            host.button("shift", True)
            host.button("oct_mod", True)
            if host.enabled:
                play(host, MODIFIER_COUNT)
            host.button("oct_mod", False)
            host.button("shift", False)
        self.assertEqual(host.engine.held_notes(), ())
        self.assertFalse(host.enabled)

    def test_octave_moves_a_held_root(self):
        host = Host()
        host.button("shift", True)
        host.button("oct_mod", True)
        play(host, MODIFIER_COUNT)
        moved = host.button("octave_up", True)
        self.assertEqual(sorted(ons(moved.events)), [72, 76, 79])
        self.assertEqual(sorted(offs(moved.events)), [60, 64, 67])

    def test_normal_play_after_orchid_is_through(self):
        host = Host()
        host.button("shift", True)
        host.button("oct_mod", True)
        host.button("oct_mod", False)
        host.button("shift", False)
        host.button("shift", True)
        host.button("oct_mod", True)
        after = play(host, 20)
        self.assertEqual(ons(after.events), [host.input_base + 20])
        self.assertFalse(after.enabled)


if __name__ == "__main__":
    unittest.main()
