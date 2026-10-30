# Progress

Phase: C and D are implemented and tested. Stock 5.0.0.2084 and SuperFreaker
0.1.2 both reach `main()` under Renode 1.17. A native patch is still blocked
on a code cave larger than 259 bytes that does not collide with SuperFreaker.

## Done

- Read `instructions.txt`.
- Confirmed this repo had no earlier plan, safety notes, or firmware.
- Cloned microfreak-emu `9f80bc3`, microfreak-tools `396fcf4`, and
  ChoralRoot `bd7f431` under `third_party/` (gitignored).
- Implemented `src/orchid/chords.py`, `engine.py`, `layout.py`, `midi_host.py`.
- 39 unit tests passed via `python scripts/verify_orchid.py`.
- Recorded the empty patch manifest and the addresses that must stay untouched.

- Verified the stock `.mff` container and payload hashes.
- Diffed SuperFreaker 0.1.2: 5,705 bytes, main image only. Recorded the
  ranges in `firmware/superfreaker_v0_1_2_ranges.json`. Coprocessors match
  stock. The speech cave is untouched. Their shift-lock site is reserved.

## Not done

- A code cave larger than the 259-byte speech tail, accepted by
  `firmware/coexist.py`, and shown by disassembly to be unused.
- Any keyboard-frame injector for the 25 keys.
- Any changed firmware byte. No Orchid image exists.

## Latest test

`python scripts/verify_orchid.py`

- unit tests: PASS (39 ran, 0 failed, 0 errors)
- stock firmware boot: PASS (`main()` at 6,915,574 instructions, PC `0x08023444`)
- SuperFreaker 0.1.2 boot: PASS (`main()` at 6,915,727 instructions, PC `0x08024FB6`)
- native patch: BLOCKED
- hardware flash: NOT RUN

## Next

Find a placement `firmware/coexist.py` accepts that is larger than 259 bytes,
and show from the disassembly that the firmware does not execute it. Then
assemble the smallest hook: one root key becomes one chord through the
firmware note path. Boot that third image. Do not write it to a device.
