# Tasks

## Active

1. Place the smallest Orchid hook that turns one root into one chord through
   the firmware note path. The measured room is the speech tail: 259 bytes
   after retiring bank 4's last word, more only by retiring further whole
   words and updating the descriptor. `firmware/coexist.py` must still allow
   the bytes.
2. Boot that third image and compare its notes with the Python engine.
3. Find the OCT | MOD panel id and the keyboard coprocessor frame from a
   trace. Do not invent either.

## Completed

- Free-flash measurement. No unused hole. The 259-byte cave is bank 4's last
  word (258 bytes) plus the byte that lands on `0x0807B367`. Two words free
  450 bytes; three free 684. Scanner spans that look larger still contain
  instructions, including a false hole inside `0x0807B368`–`0x0807C84C`.
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
