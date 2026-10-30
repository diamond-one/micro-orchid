# Tasks

## Active

1. Find the OCT | MOD panel id and the keyboard coprocessor frame from a
   trace. Do not invent either.

## Completed

- Major-triad hook. Retires bank 4's last word, branches from the MIDI
  channel callback at `0x080478EA`, and calls the existing note handler for
  the root, the third, and the fifth. Renode: note 60 on and off produced
  60, 64, 67, matching `spell(60)`. The downloaded images were not modified.
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

- The rest of Orchid Mode in firmware: qualities, extensions, inversions,
  latch, strum, and arp. One retired word is not enough room.
- Emulator sequence that shows one root plus modifiers producing the chord
  from patched firmware, not from this Python process.
- Independent review after a patch exists.
- Physical flash. Not authorized.
