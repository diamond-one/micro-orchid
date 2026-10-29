# Progress

Phase: C and D are implemented and tested. A, B, and E through H are blocked
on the stock firmware image, Renode, and a usable code cave.

## Done

- Read `instructions.txt`.
- Confirmed this repo had no earlier plan, safety notes, or firmware.
- Cloned microfreak-emu `9f80bc3`, microfreak-tools `396fcf4`, and
  ChoralRoot `bd7f431` under `third_party/` (gitignored).
- Implemented `src/orchid/chords.py`, `engine.py`, `layout.py`, `midi_host.py`.
- 39 unit tests passed via `python scripts/verify_orchid.py`.
- Recorded the empty patch manifest and the addresses that must stay untouched.

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
