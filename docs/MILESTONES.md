# Milestones

| Id | Status | Evidence |
|---|---|---|
| M1 Development environment | BLOCKED | Python, Git, and Java are present. uv, Renode, REA, Ghidra, mfreak, and the stock image are not. See `docs/ENVIRONMENT.md`. |
| M2 Emulator | BLOCKED | `microfreak-emu` is cloned. It was not booted. Renode is missing and `firmware/stock/` is empty. |
| M3 Chord engine | PASS | `python scripts/verify_orchid.py` — 39 tests, 0 failures. Covers the four-voice examples, all 12 roots, qualities, extensions, inversions, latch, shared pitches, strum cancel, and arp. |
| M4 Host MIDI | PASS for the virtual host. Hardware NOT RUN | `tests/test_midi_host.py` drives Shift+OCT\|MOD, chords, release, octave, and channel isolation through `Host`. No MIDI interface was opened. |
| M5 Native integration | BLOCKED | No image, no ARM compiler, documented cave is 259 bytes. Manifest is empty. |
| M6 Orchid Mode in firmware | BLOCKED | Depends on M5. The host demonstrates the control, which is not firmware execution. |
| M7 Regression and safety | PARTIAL | Unit tests and the empty-manifest check pass. Emulator regression was not run. No independent second agent reviewed the code in this session. |
| M8 Release candidate | BLOCKED | There is no patched image, no image hash, and no byte manifest of changes. |
| M9 Hardware | NOT RUN | Flashing was not authorized. |

M3 and the virtual half of M4 are the working software. They are not a
firmware release.
