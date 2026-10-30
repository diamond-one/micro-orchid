# Tasks

## Active

1. Find the OCT | MOD panel id and the keyboard coprocessor frame from a
   trace. Do not invent either. The mode image has 51 bytes free after
   `0x0807B334`, which is not enough for a keyboard parser.

## Completed

- Orchid Mode in the speech tail. Retires the last 17 words of bank 4
  (size `0x39A`, code at `0x0807A440`, 3,828 bytes, ends `0x0807B334`).
  Branches from the MIDI channel callback at `0x080478EA` and calls the
  existing note handler. Both stack tops (`0x0800C000` and `0x0805F884`)
  move to `0x2001FE00` so the engine state and the mailbox at
  `0x2001FF00` stay above the stack. Renode matched the Python engine:
  note 60 on played 60, 64, 67; inversion up released 60 and played 72;
  panic released 64, 67, 72; minor played 60, 63, 67; a minor seventh
  added 70. The downloaded images were not modified.
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
- The same engine in C, checked against the Python cases through a host DLL.
- Shift+OCT|MOD behavior on the host, including power-on with the combo held.
- Safety boundaries and the five-range mode manifest.
- Verification command: `python scripts/verify_orchid.py`.

## Waiting

- Latch, strum, and arp driven inside Renode. The code is in the image.
- A keyboard parser, after a trace supplies the 25 key ids and after more
  of bank 4 is retired if the parser needs the room.
- Independent review.
- Physical flash. Not authorized.
