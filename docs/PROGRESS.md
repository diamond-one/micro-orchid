# Progress

Phase: Orchid Mode is in a SuperFreaker image and matched the Python
engine under Renode for a major triad, an inversion, panic, a minor
triad, and a minor seventh. Stock 5.0.0.2084 and SuperFreaker 0.1.2
both still reach `main()`. The panel key ids are still unknown, so the
booted image takes modifiers through a four-byte mailbox.

## Done

- Read `instructions.txt`.
- Confirmed this repo had no earlier plan, safety notes, or firmware.
- Cloned microfreak-emu `9f80bc3`, microfreak-tools `396fcf4`, and
  ChoralRoot `bd7f431` under `third_party/` (gitignored).
- Implemented `src/orchid/chords.py`, `engine.py`, `layout.py`, `midi_host.py`.
- Ported that engine to `firmware/orchid_engine.c`. The host DLL matches
  the Python cases. The device build is the same source with
  `-DORCHID_DEVICE`.
- 65 unit tests passed via `python -m unittest discover -s tests`.
- The patch manifest lists the mode image's five ranges. No firmware bytes.
- Verified the stock `.mff` container and payload hashes.
- Diffed SuperFreaker 0.1.2: 5,705 bytes, main image only. Recorded the
  ranges in `firmware/superfreaker_v0_1_2_ranges.json`. Coprocessors match
  stock. The speech cave is untouched by SuperFreaker. Their shift-lock
  site is reserved.
- Measured the mode at 3,828 bytes with `-Oz -flto`. Seventeen bank-4
  words leave 3,881 bytes; sixteen leave 3,601 and do not fit. The image
  keeps the first five words of that bank. Colors, numbers, letters, and
  the four musical voices stay.

## Not done

- A keyboard-frame parser. The linked code ends at `0x0807B334`, which
  leaves 51 bytes before `0x0807B367`. That is not enough for a parser,
  and the 25 key ids are still unknown.
- Latch, strum, and arp on the emulated chip. They are in this image and
  covered by the host tests. The Renode script has not driven them.
- A stored Orchid image. The booted payload was a temp file. The downloads
  were not modified.

## Latest test

`python -m unittest discover -s tests` and `python scripts/boot_triad.py`

- unit tests: PASS (65 ran, 0 failed, 0 errors)
- stock firmware boot: PASS (`main()` at 6,915,574 instructions, PC `0x08023444`)
- SuperFreaker 0.1.2 boot: PASS (`main()` at 6,915,727 instructions, PC `0x08024FB6`)
- mode image: PASS. Reached `main()`. Against the Python engine, note 60
  played 60, 64, 67; inversion up released 60 and played 72; panic released
  64, 67, 72; minor played 60, 63, 67; adding a minor seventh played 70.
- hardware flash: NOT RUN

## Next

The panel key ids still have to come from a trace. Do not invent them.
Do not write an image to a device.
