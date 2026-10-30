# Progress

Phase: C and D are implemented and tested. Stock 5.0.0.2084 and SuperFreaker
0.1.2 both reach `main()` under Renode 1.17. Free flash was measured: the
only room is the speech-bank tail. A native patch is not built yet.

## Done

- Read `instructions.txt`.
- Confirmed this repo had no earlier plan, safety notes, or firmware.
- Cloned microfreak-emu `9f80bc3`, microfreak-tools `396fcf4`, and
  ChoralRoot `bd7f431` under `third_party/` (gitignored).
- Implemented `src/orchid/chords.py`, `engine.py`, `layout.py`, `midi_host.py`.
- 47 unit tests passed via `python -m unittest discover -s tests`.
- Recorded the empty patch manifest and the addresses that must stay untouched.

- Verified the stock `.mff` container and payload hashes.
- Diffed SuperFreaker 0.1.2: 5,705 bytes, main image only. Recorded the
  ranges in `firmware/superfreaker_v0_1_2_ranges.json`. Coprocessors match
  stock. The speech cave is untouched. Their shift-lock site is reserved.

## Not done

- The smallest hook: one root becomes one chord through the note path,
  placed in the 259-byte speech tail or in a larger tail made by retiring
  more whole words of bank 4.
- Any keyboard-frame injector for the 25 keys.
- Any changed firmware byte. No Orchid image exists.

## Latest test

`python scripts/verify_orchid.py`

- unit tests: PASS (47 ran, 0 failed, 0 errors)
- stock firmware boot: PASS (`main()` at 6,915,574 instructions, PC `0x08023444`)
- SuperFreaker 0.1.2 boot: PASS (`main()` at 6,915,727 instructions, PC `0x08024FB6`)
- native patch: BLOCKED
- hardware flash: NOT RUN

## Next

Assemble the smallest hook: one root key becomes one chord through the
firmware note path. Place it in `0x0807B264`–`0x0807B367` if it fits. If
it does not, retire more whole words of bank 4 and update that bank's size.
Boot that third image. Do not write it to a device. Do not use a span the
reachability walk missed; those spans are still code.
