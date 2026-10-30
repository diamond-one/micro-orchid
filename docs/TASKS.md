# Tasks

## Active

1. Measure free flash on the SuperFreaker image. Do not assume the 259-byte
   speech cave is the only gap, and do not assume a zero-filled region is unused.
2. Place the smallest Orchid hook that turns one root into one chord through
   the firmware note path, on bytes `firmware/coexist.py` still allows.
3. Boot that third image and compare its notes with the Python engine.
4. Find the OCT | MOD panel id and the keyboard coprocessor frame from a
   trace. Do not invent either.

## Completed

- uv, clang, and Renode 1.17. Stock `mfemu check` is READY. Stock and
  SuperFreaker 0.1.2 both reach `main()` in Renode. No device write.
- Chord spelling, four-voice reduction, engine lifecycle, virtual host.
- Shift+OCT|MOD behavior on the host, including power-on with the combo held.
- Safety boundaries and an empty patch manifest.
- Verification command: `python scripts/verify_orchid.py`.

## Waiting

- Native hook at the MIDI dispatch or the keyboard path.
- Emulator sequence that shows one root plus modifiers producing the chord
  from patched firmware, not from this Python process.
- Independent review after a patch exists.
- Physical flash. Not authorized.
