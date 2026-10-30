# Progress

Phase: C and D are implemented and tested. The stock image and SuperFreaker
0.1.2 have been identified and diffed. A native patch is still blocked on
Renode, an ARM assembler, and a code cave larger than 259 bytes that does
not collide with SuperFreaker.

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

- `uv sync`, `mfemu check`, `mfemu boot`.
- Any boot of stock or patched firmware.
- Any keyboard-frame injector for the 25 keys.
- Any changed firmware byte.

## Latest test

`python scripts/verify_orchid.py`

- unit tests: PASS (39 ran, 0 failed, 0 errors)
- stock firmware: BLOCKED
- emulator boot: BLOCKED
- native patch: BLOCKED
- hardware flash: NOT RUN

## Next command, once a stock `.mff` is in `firmware/stock/` and Renode is installed

```
uv sync
uv run mfemu check --firmware ../../firmware/stock/<official>.mff
uv run mfemu boot --firmware ../../firmware/stock/<official>.mff
```

Run those from a microfreak-emu checkout whose sibling is microfreak-tools,
as that repo's README requires. Do not point them at an image whose payload
sha256 is not `54be2e0b695e2279602513e1a9ed39906408ba221a45e782b61273f0ef55d15f`
unless the addresses in `docs/ARCHITECTURE.md` have been re-derived.
