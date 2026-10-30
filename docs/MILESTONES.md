# Milestones

| Id | Status | Evidence |
|---|---|---|
| M1 Development environment | PARTIAL | uv, clang 23.1.4, and Renode 1.17.0 are installed. REA, Ghidra, and mfreak are still absent. |
| M2 Emulator | PASS for boot | Stock 5.0.0.2084 reached `main()` at 6,915,574 instructions. SuperFreaker 0.1.2 reached `main()` at 6,915,727. Both entered at `0x0800C000` with no bootloader. The images stayed in Downloads. |
| M3 Chord engine | PASS | `python -m unittest discover -s tests` — 65 tests, 0 failures. Covers the four-voice examples, all 12 roots, qualities, extensions, inversions, latch, shared pitches, strum cancel, arp, and the C engine against those cases. |
| M4 Host MIDI | PASS for the virtual host. Hardware NOT RUN | `tests/test_midi_host.py` drives Shift+OCT\|MOD, chords, release, octave, and channel isolation through `Host`. No MIDI interface was opened. |
| M5 Native integration | PARTIAL | `scripts/boot_triad.py` reached `main()` on the mode image. Major, inversion, panic, minor, a minor seventh, latch, strum, and arp matched the Python engine. Modifiers arrive through the mailbox at `0x2001FF00`. The 25 key ids are still unknown. |
| M6 Orchid Mode in firmware | PARTIAL | The 3,828-byte engine is in the image and Renode has run qualities, an extension, inversion, latch, strum, and arp. The Shift+OCT\|MOD toggle is not in the image. |
| M7 Regression and safety | PARTIAL | 65 unit tests pass. The mode boot matched the engine on the sequences above. The five patch ranges were checked against `placement_ok` and against PC-relative SRAM loads. No second person has reviewed the code. |
| M8 Release candidate | BLOCKED | The booted temp payload sha256 is `cc6e64a52b9d7042c574ae0c8cd4fe4aec7a8347dd10c6959d2199870e5e4c89` (473,695 bytes). It is not stored here, and it has no keyboard entry, so it is not a release candidate. |
| M9 Hardware | NOT RUN | Flashing was not authorized. |

M3 and the virtual half of M4 are the working software. They are not a
firmware release.
