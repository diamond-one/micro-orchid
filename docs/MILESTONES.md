# Milestones

| Id | Status | Evidence |
|---|---|---|
| M1 Development environment | PARTIAL | uv, clang 23.1.4, and Renode 1.17.0 are installed. REA, Ghidra, and mfreak are still absent. |
| M2 Emulator | PASS for boot | Stock 5.0.0.2084 reached `main()` at 6,915,574 instructions. SuperFreaker 0.1.2 reached `main()` at 6,915,727. Both entered at `0x0800C000` with no bootloader. The images stayed in Downloads. |
| M3 Chord engine | PASS | `python -m unittest discover -s tests` — 69 tests, 0 failures. Covers the four-voice examples, all 12 roots, qualities, extensions, inversions, latch, shared pitches, strum cancel, arp, the C engine against those cases, and the measured key-index notes. |
| M4 Host MIDI | PASS for the virtual host. Hardware NOT RUN | `tests/test_midi_host.py` drives Shift+OCT\|MOD, chords, release, octave, and channel isolation through `Host`. No MIDI interface was opened. |
| M5 Native integration | PARTIAL | `scripts/boot_triad.py` reached `main()` on the mode image. Major, inversion, panic, minor, a minor seventh, latch, strum, and arp matched the Python engine. Key 12 played that major triad, key 1 made it minor, and the release cleared it. Unarmed, key 12 is one note. Shift plus `0x0401` armed it, and the same shortcut disarmed it. |
| M6 Orchid Mode in firmware | PARTIAL | The 4,320-byte engine is in the image and Renode has run qualities, an extension, inversion, latch, strum, arp, the keyboard layout, and the Shift+Oct\|Mod toggle. The display does not yet show `ORCHID ON` or `ORCHID OFF`. |
| M7 Regression and safety | PARTIAL | 69 unit tests pass. The mode boot matched the engine on the sequences above. The eight patch ranges were checked against `placement_ok` and against PC-relative SRAM loads. No second person has reviewed the code. |
| M8 Release candidate | BLOCKED | The booted payload is a temp file and is not stored here. The toggle is in it. The display text is not, so it is not a release candidate. |
| M9 Hardware | NOT RUN | Flashing was not authorized. |

M3 and the virtual half of M4 are the working software. They are not a
firmware release.
