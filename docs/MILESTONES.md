# Milestones

| Id | Status | Evidence |
|---|---|---|
| M1 Development environment | PARTIAL | uv, clang 23.1.4, and Renode 1.17.0 are installed. REA, Ghidra, and mfreak are still absent. |
| M2 Emulator | PASS for boot | Stock 5.0.0.2084 reached `main()` at 6,915,574 instructions. SuperFreaker 0.1.2 reached `main()` at 6,915,727. Both entered at `0x0800C000` with no bootloader. The images stayed in Downloads. |
| M3 Chord engine | PASS | `python -m unittest discover -s tests` — 52 tests, 0 failures. Covers the four-voice examples, all 12 roots, qualities, extensions, inversions, latch, shared pitches, strum cancel, and arp. |
| M4 Host MIDI | PASS for the virtual host. Hardware NOT RUN | `tests/test_midi_host.py` drives Shift+OCT\|MOD, chords, release, octave, and channel isolation through `Host`. No MIDI interface was opened. |
| M5 Native integration | PARTIAL | One MIDI note becomes a major triad. `scripts/boot_triad.py` reached `main()` and note 60 on and off matched `spell(60)`: 60, 64, 67. The hook is 110 bytes in the retired word. |
| M6 Orchid Mode in firmware | BLOCKED | The triad is the only firmware behavior. Qualities, inversions, latch, strum, and arp are still host-only. |
| M7 Regression and safety | PARTIAL | 52 unit tests pass. The triad boot matched the engine. No independent second agent reviewed the code. |
| M8 Release candidate | BLOCKED | The booted payload was a temp file. It is not stored here, and it has no published hash. |
| M9 Hardware | NOT RUN | Flashing was not authorized. |

M3 and the virtual half of M4 are the working software. They are not a
firmware release.
