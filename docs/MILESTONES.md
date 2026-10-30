# Milestones

| Id | Status | Evidence |
|---|---|---|
| M1 Development environment | PARTIAL | uv, clang 23.1.4, and Renode 1.17.0 are installed. REA, Ghidra, and mfreak are still absent. |
| M2 Emulator | PASS for boot | Stock 5.0.0.2084 reached `main()` at 6,915,574 instructions. SuperFreaker 0.1.2 reached `main()` at 6,915,727. Both entered at `0x0800C000` with no bootloader. The images stayed in Downloads. |
| M3 Chord engine | PASS | `python -m unittest discover -s tests` — 69 tests, 0 failures. Covers the four-voice examples, all 12 roots, qualities, extensions, inversions, latch, shared pitches, strum cancel, arp, the C engine against those cases, and the measured key-index notes. |
| M4 Host MIDI | PASS for the virtual host. Hardware NOT RUN | `tests/test_midi_host.py` drives Shift+OCT\|MOD, chords, release, octave, and channel isolation through `Host`. No MIDI interface was opened. |
| M5 Native integration | PASS for the emulated image | `scripts/boot_triad.py` reached `main()` on the mode image. Before any button frame, key 12 was one note. Major, inversion, panic, minor, a minor seventh, latch, strum, and arp matched the Python engine. Key 12 played that major triad, key 1 made it minor, and the release cleared it. Shift plus `0x0401` armed it, showed `ORCHID ON`, and the same shortcut disarmed it and showed `ORCHID OFF`. A fast Shift double-tap left the stock shift flag set, and Oct\|Mod then showed `ORCHID ON` and played the triad. With the arpeggiator on, Oct\|Mod alone still opened the range page and the shortcut showed `ORCHID ON`. With the sequencer on, the shortcut showed `ORCHID ON` and left the sequencer selected. |
| M6 Orchid Mode in firmware | PASS for the emulated image | The 4,569-byte engine is in the image. Renode has run qualities, an extension, inversion, latch, strum, arp, the keyboard layout, and the Shift+Oct\|Mod toggle. That shortcut reconstructed as `ORCHID ON`, and the next one as `ORCHID OFF`. |
| M7 Regression and safety | PASS for the eight ranges | 69 unit tests pass. The mode boot matched the engine. An independent review accepted all eight ranges and the three gaps left out of the image. It found a repeated Oct\|Mod down reaching the stock handler, and button statics that a reset does not clear. Both were fixed in the mode image. |
| M8 Release candidate | PASS for the offline recipe | `scripts/release_recipe.py` rebuilds the image in memory and prints the hash. The eight ranges were accepted. The payload is not stored. Flash is not approved. |
| M9 Hardware | NOT RUN | Flashing was not authorized. |

M3 and the virtual half of M4 are the working software. They are not a
firmware release.
