# Progress

Phase: Orchid Mode is in a SuperFreaker image. Under Renode it matched
the Python engine for a major triad, an inversion, panic, a minor triad,
a minor seventh, latch, strum, and arp. Stock 5.0.0.2084 and
SuperFreaker 0.1.2 both still reach `main()`. The 25 key ids and the
OCT | MOD id are still unknown, so the booted image takes modifiers
through a four-byte mailbox.

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

- A keyboard parser. The linked code ends at `0x0807B334`, which leaves
  51 bytes before `0x0807B367`. The id search is recorded in
  `docs/BLOCKERS.md`.
- A stored Orchid image. The booted payload was a temp file. Its sha256 is
  `cc6e64a52b9d7042c574ae0c8cd4fe4aec7a8347dd10c6959d2199870e5e4c89`.
  The downloads were not modified. That hash is not a release candidate.

## Latest test

`python -m unittest discover -s tests` and `python scripts/boot_triad.py`

- unit tests: PASS (65 ran, 0 failed, 0 errors)
- stock firmware boot: PASS (`main()` at 6,915,574 instructions, PC `0x08023444`)
- SuperFreaker 0.1.2 boot: PASS (`main()` at 6,915,727 instructions, PC `0x08024FB6`)
- mode image: PASS. Reached `main()`. Against the Python engine: note 60
  played 60, 64, 67; inversion up released 60 and played 72; panic released
  64, 67, 72; minor played 60, 63, 67; a minor seventh added 70; latch kept
  minor after the key lift and returned to major when latch cleared; strum
  played 60, then 64, and a root release cancelled the rest; arp played 60
  and the next step released 60 and played 64.
- placement review: the only PC-relative SRAM load at or above `0x2001FE00`
  is the startup stack word at `0x0805F884`, which the patch updates with
  the vector. The next-highest pool word is `0x2001F230`. `placement_ok`
  accepts the five ranges.
- hardware flash: NOT RUN

## Next

The panel key ids still have to come from a trace. Do not invent them.
Do not write an image to a device.
