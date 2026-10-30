# Tasks

## Active

1. Find the OCT | MOD panel id from a trace. Do not invent it. Key frames
   are measured; that button is not.

## Completed

- Keyboard frames. Subcommand `0x05` is key down and `0x06` is key up.
  Index n sounds as MIDI note n+48. The mode branches at `0x0803AD9E`.
  Mailbox op 7 arms the layout: indexes 0-11 are modifiers and 12-24 are
  roots. Unarmed, the key stays one stock note.
- Orchid Mode in the speech tail. Retires the last 18 words of bank 4
  (size `0x2E8`, code at `0x0807A38C`, 3,924 bytes, ends `0x0807B2E0`).
  Branches from the MIDI channel callback at `0x080478EA` and from the
  key-note call at `0x0803AD9E`. Both stack tops (`0x0800C000` and
  `0x0805F884`) move to `0x2001FE00` so the engine state and the mailbox
  at `0x2001FF00` stay above the stack. The MIDI boot matched the Python
  engine. The same run then armed the keyboard: key 12 played 60, 64, 67;
  key 1 moved the third from 64 to 63; the key release cleared the chord;
  with the layout disarmed, key 12 played only 60. The downloaded images
  were not modified.
- Major-triad hook, kept as the smaller reference. It retires bank 4's
  last word only and is 110 bytes. The mode image is what `boot_triad.py`
  builds now.
- Free-flash measurement. No unused hole. The 259-byte cave is bank 4's
  last word (258 bytes) plus the byte that lands on `0x0807B367`. Scanner
  spans that look larger still contain instructions, including a false
  hole inside `0x0807B368`–`0x0807C84C`.
- uv, clang, and Renode 1.17. Stock `mfemu check` is READY. Stock and
  SuperFreaker 0.1.2 both reach `main()` in Renode. No device write.
- Chord spelling, four-voice reduction, engine lifecycle, virtual host.
- Latch, strum, and arp on the emulated chip, through the same mailbox.
  Latch kept a minor chord after the key lift. Strum played the root,
  then the third, and a release cancelled the fifth. Arp stepped from
  60 to 64.
- The same engine in C, checked against the Python cases through a host DLL.
- Shift+OCT|MOD behavior on the host, including power-on with the combo held.
- Safety boundaries and the six-range mode manifest.
- Verification command: `python scripts/verify_orchid.py`.

## Waiting

- The OCT | MOD panel id. Key frames are measured. Do not invent the button.
- A second person's review. The six ranges were checked locally against
  `placement_ok` and the SRAM literal pools.
- Physical flash. Not authorized.
