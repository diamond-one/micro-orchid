# Architecture

```
physical or virtual keys
        |
        v
  midi_host.Host          Shift+OCT|MOD, octave, hold, channel split
        |
        v
  engine.Engine           latch, inversion, bass, arp, voice cap, note lifecycle
        |
        v
  chords.spell            qualities, extensions, four-voice reduction
```

`spell` is pure. The same inputs always return the same notes. `Engine`
turns key transitions into note-on and note-off events. `Host` is the
playable reference. It is not firmware.

A native patch, when a stock image and a real code cave exist, should call
the same musical rules. Until then `firmware/boundaries.py` is only the
forbidden address ranges and an empty change manifest.

The emulator path is `third_party/microfreak-emu`, pinned in
`docs/ENVIRONMENT.md`. It runs the main STM32 image. It does not run the
keyboard, matrix, or OLED coprocessors. A MIDI chord sent into that
emulator would prove the synthesizer can sound notes. It would not prove
that the keyboard was remapped. That proof needs a keyboard-event injector
built from the real coprocessor protocol, which is not known for the 25 keys.

## Firmware addresses, not re-traced here

These are copied from `microfreak-emu` `docs/FIRMWARE.md` and
`microfreak-tools` `microfreak/firmware/patching.py` for 5.0.0.2084.
Confidence is "published by those repos", not "executed in this session".

| Address | What those repos say |
|---|---|
| `0x08000000`–`0x08007FFF` | bootloader, do not touch |
| `0x08008000`–`0x0800BFFF` | factory data, do not touch |
| `0x0800C000` | application vector table |
| `0x0802479C` | `main` |
| `0x080478A4` | MIDI note dispatch |
| `0x080480A8` | MIDI byte parser |
| `0x08048524` | voice handler |
| `0x0807B264`–`0x0807B367` | speech-vocabulary cave used by `mfreak fw patch` |

Shift on the panel injector is control id `0x0804` in
`mfemu/frontpanel.py`. OCT | MOD is not in that table.
