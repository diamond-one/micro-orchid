# Tasks

## Active

1. Install Renode and an ARM assembler, then boot stock and SuperFreaker
   without writing either image to a device.
2. Install uv and Renode, then run the stock `mfemu check` and `mfemu boot`.
3. With the image in hand, measure free flash. Do not assume the 259-byte
   speech cave is the only gap, and do not assume a zero-filled region is unused.
4. Find the OCT | MOD panel id and the keyboard coprocessor frame from a
   trace. Do not invent either.

## Completed

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
