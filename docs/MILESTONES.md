# Milestones

| Id | Status | Evidence |
|---|---|---|
| M1 Development environment | PARTIAL | uv, clang 23.1.4, and Renode 1.17.0 are installed. REA, Ghidra, and mfreak are still absent. |
| M2 Emulator | PASS for boot | Stock 5.0.0.2084 reached `main()` at 6,915,574 instructions. SuperFreaker 0.1.2 reached `main()` at 6,915,727. Both entered at `0x0800C000` with no bootloader. The images stayed in Downloads. |
| M3 Chord engine | PASS | `python -m unittest discover -s tests` — 47 tests, 0 failures. Covers the four-voice examples, all 12 roots, qualities, extensions, inversions, latch, shared pitches, strum cancel, and arp. |
| M4 Host MIDI | PASS for the virtual host. Hardware NOT RUN | `tests/test_midi_host.py` drives Shift+OCT\|MOD, chords, release, octave, and channel isolation through `Host`. No MIDI interface was opened. |
| M5 Native integration | BLOCKED | clang can target Thumb-2. The only measured room is the speech tail, 259 bytes unless more bank-4 words are retired. No hook is placed. Manifest is empty. |
| M6 Orchid Mode in firmware | BLOCKED | Depends on M5. The host demonstrates the control, which is not firmware execution. |
| M7 Regression and safety | PARTIAL | Unit tests and the empty-manifest check pass. Emulator regression was not run. No independent second agent reviewed the code in this session. |
| M8 Release candidate | BLOCKED | There is no patched image, no image hash, and no byte manifest of changes. |
| M9 Hardware | NOT RUN | Flashing was not authorized. |

M3 and the virtual half of M4 are the working software. They are not a
firmware release.
