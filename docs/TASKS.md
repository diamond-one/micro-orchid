# Tasks

## Active

1. Read the independent review of the eight patch ranges and keep the
   recipe in `docs/RELEASE.md` aligned with it. Flash stays unauthorized.

## Completed

- Panel text. Shift plus `0x0401` sends `ORCHID ON`, and the same
  shortcut sends `ORCHID OFF`, through the frame builder at
  `0x080226D0`. Renode reconstructed both strings. The button alone
  still opens the stock screen and does not draw those words.
- Keyboard frames. Subcommand `0x05` is key down and `0x06` is key up.
  Index n sounds as MIDI note n+48. The mode branches at `0x0803AD9E`.
  Mailbox op 7 arms the layout: indexes 0-11 are modifiers and 12-24 are
  roots. Unarmed, the key stays one stock note.
- Orchid Mode in the speech tail. Retires the last 21 words of bank 4
  (size `0xC6`, code at `0x0807A16C`, 4,493 bytes, ends `0x0807B2F9`).
  Branches from the MIDI channel callback at `0x080478EA`, the key-note
  call at `0x0803AD9E`, and the button edges at `0x0804348C` and
  `0x080434A4`. Both stack tops (`0x0800C000` and `0x0805F884`) move to
  `0x2001FE00`. The MIDI boot matched the Python engine. Key 12 played
  60, 64, 67; key 1 moved the third from 64 to 63. Shift plus `0x0401`
  armed the layout and the same shortcut released the chord. Shift
  alone and that button alone left key 12 as one note. The downloaded
  images were not modified.
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
- Safety boundaries and the eight-range mode manifest.
- Verification command: `python scripts/verify_orchid.py`.

## Waiting

- Physical flash. Not authorized.
