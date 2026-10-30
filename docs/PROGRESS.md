# Progress

Phase: the major-triad hook is in firmware and matched the Python engine
under Renode. Stock 5.0.0.2084 and SuperFreaker 0.1.2 both still reach
`main()`. The rest of Orchid Mode is not in the image.

## Done

- Read `instructions.txt`.
- Confirmed this repo had no earlier plan, safety notes, or firmware.
- Cloned microfreak-emu `9f80bc3`, microfreak-tools `396fcf4`, and
  ChoralRoot `bd7f431` under `third_party/` (gitignored).
- Implemented `src/orchid/chords.py`, `engine.py`, `layout.py`, `midi_host.py`.
- 52 unit tests passed via `python -m unittest discover -s tests`.
- The patch manifest lists the triad hook's three ranges. No firmware bytes.

- Verified the stock `.mff` container and payload hashes.
- Diffed SuperFreaker 0.1.2: 5,705 bytes, main image only. Recorded the
  ranges in `firmware/superfreaker_v0_1_2_ranges.json`. Coprocessors match
  stock. The speech cave is untouched. Their shift-lock site is reserved.

## Not done

- Qualities, extensions, inversions, latch, strum, and arp in firmware.
  They do not fit in the 259 bytes this one word freed.
- Any keyboard-frame injector for the 25 keys.
- A stored Orchid image. The booted payload was a temp file. The downloads
  were not modified.

## Latest test

`python -m unittest discover -s tests` and `python scripts/boot_triad.py`

- unit tests: PASS (52 ran, 0 failed, 0 errors)
- stock firmware boot: PASS (`main()` at 6,915,574 instructions, PC `0x08023444`)
- SuperFreaker 0.1.2 boot: PASS (`main()` at 6,915,727 instructions, PC `0x08024FB6`)
- triad image: PASS. MIDI note 60 on and off produced 60, 64, 67, matching `spell(60)`.
- hardware flash: NOT RUN

## Next

The panel key ids still have to come from a trace. The rest of Orchid Mode
needs more than the one retired word, which is a separate decision. Do not
write an image to a device.
