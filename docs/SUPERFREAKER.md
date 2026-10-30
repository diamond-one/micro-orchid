# SuperFreaker 0.1.2 beside Orchid

Measured from the two files supplied for this machine. The firmware bytes
are not in this repository. Re-check with:

```powershell
python scripts/inspect_firmware.py `
  C:\Users\thisi\Downloads\MicroFreak_Firmware_Update_5_0_0_2084.mff `
  C:\Users\thisi\Downloads\superfreaker_v0_1_2_5_0_0_2084.mff `
  --check firmware/superfreaker_v0_1_2_ranges.json
```

## What the files are

| File | sha256 of the `.mff` | Main payload sha256 |
|---|---|---|
| Stock `MicroFreak_Firmware_Update_5_0_0_2084.mff` | `c2b405e3c8565b7b73b4dd06522559458190082a8ba633cc5f1bcc43dc64332c` | `54be2e0b695e2279602513e1a9ed39906408ba221a45e782b61273f0ef55d15f` |
| `superfreaker_v0_1_2_5_0_0_2084.mff` | `e596126d4b60328b2197448d34fe8a994f5e3761d517b828626992a4eb5d20dc` | `00977cbb023f680500ab1c151342a7df5f462d9355e408e8c59b96e2d12c8c19` |

The stock container hash is the digest quoted in the mission notes. The
payload hash is the one `microfreak-tools` requires. Both matched. The main
payload is 473,695 bytes, loaded at `0x0800C000`. `info.json` in both files
still says version 5.0.0.2084, dated 2023_05_30.

## How SuperFreaker adds its features

Only image 0, the main application, changes. The OLED, matrix, and keyboard
coprocessors, and the factory wavetable bank, are byte-identical to stock.
The bootloader is not in either file.

5,705 bytes differ, in 227 ranges. The pattern is:

- One dense rewrite from `0x0802B8F0` to `0x0802EF30`. New strings there
  name the added behavior: reverb, echo, tape wobble, legato glide, sub
  octave, lo-fi, tremolo, ignore program change, ignore MIDI start.
- About fifty branches outside that window are retargeted into it. Those
  are the hooks. One of them is at `0x08047A34`, inside the MIDI area.
  The entries `microfreak-emu` calls note dispatch (`0x080478A4`), the MIDI
  parser (`0x080480A8`), and the voice handler (`0x08048524`) still begin
  with the same 16 bytes as stock.
- The boot line at `0x080757AC` becomes `SUPERFREAKER` / `v0.1.2`.
- Around `0x080387A4` the shift path is replaced and the image gains
  `Shift / LOCK OFF` and `Shift / LOCK ON`.

The speech-vocabulary table at `0x08078838` is unchanged, and the 259-byte
cave at `0x0807B264` is unchanged. SuperFreaker did not use the cave
`microfreak-tools` uses for its own patches.

## Living together

An Orchid build that should keep SuperFreaker has to start from the
SuperFreaker image, not from stock, and then change only bytes that are
still equal to stock outside SuperFreaker's window.

`firmware/coexist.py` rejects a placement that:

- overlaps any of the 227 recorded ranges
- sits in `0x0802B8F0`–`0x0802EF30`, including gaps SuperFreaker did not
  rewrite, because those gaps are inside its code
- writes the banner at `0x080757AC`
- writes the shift-lock handler at `0x080387A4`

The speech cave passes that test. It is still 259 bytes, and the chord
engine does not fit in it. Orchid's Shift+OCT|MOD toggle also cannot reuse
SuperFreaker's shift-lock site. The toggle has to be a new hook on a byte
range this check still allows, chained so their lock behavior still runs.

No combined image has been built. The unmodified SuperFreaker image does
boot: Renode 1.17 reached its `main()` at 6,915,727 instructions.
