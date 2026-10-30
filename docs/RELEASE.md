# Offline release recipe

This builds the mode image in memory and prints its hash. It does not
write the payload into this repository and it does not flash a device.
Flashing stays unauthorized.

From the repository root:

```
uv run python scripts/release_recipe.py
```

`scripts/boot_triad.py` is run from `third_party/microfreak-emu`, where
the emulator package is installed.

The inputs stay in Downloads:

- `MicroFreak_Firmware_Update_5_0_0_2084.mff`
- `superfreaker_v0_1_2_5_0_0_2084.mff`

`scripts/boot_triad.py` is the emulator proof. It has to reach `main()`,
match the Python engine, leave key 12 as one note before any button
frame, and reconstruct `ORCHID ON` then `ORCHID OFF`.

## What the recipe prints

The commit, the compiler, the pinned emulator and tools revisions, the
stock and SuperFreaker hashes, the mode-image hash, and the eight
ranges in `firmware/boundaries.py`. Every byte that differs from
SuperFreaker has to sit inside those ranges.

One run produced mode image
`d345023880686bb6f9fc86b4888ab21c62c89557d0bacb5610b007460f060424`.
That digest covers the whole 473,695-byte payload. Re-run the script
after any change to the C sources. A doc-only change does not move it.

## Known limitations

- Key pressure stays on the stock call at `0x0803AE28`. The sounding
  root receives that key's aftertouch. The other chord tones do not.
- A down edge after startup is a press. The bus does not report the
  level of a button already held at power-on. Reset leaves the layout
  off, and the boot checks that before any button frame.
- `ORCHID ON` and `ORCHID OFF` stay until the next stock redraw.
- Index 0 is not proven to be the leftmost physical key. Index n sounds
  as MIDI note n+48 for indexes 0, 7, 12, and 24.
- The payload is a temp result of this recipe. It is not stored here.
