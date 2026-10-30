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

## Where room actually is

A walk of reachable Thumb code, plus every address a PC-relative load
reads, does not leave an unused hole. The spans that walk misses still
disassemble as code: the largest ones contain `push` prologues or `bl`.
They are routines the walk did not reach. Treating a `push` encoding as a
new function start also decodes speech data as code, and the tail of a
live table then looks empty. One of those false holes was
`0x0807B5E0`–`0x0807BCBC`, inside the seven objects that start at
`0x0807B368`. That range stays forbidden.

The five banks are packed. On SuperFreaker 0.1.2 the descriptor is:

| Bank | Pointer | Size | Words |
|---|---|---|---|
| 0 | `0x08078860` | 1233 | 7 |
| 1 | `0x08078D34` | 900 | 11 |
| 2 | `0x080790B8` | 1552 | 26 |
| 3 | `0x080796C8` | 2524 | 26 |
| 4 | `0x0807A0A4` | 4802 | 22 |

Word counts come from `word_byte_offsets` in microfreak-tools `396fcf4`.
Nothing loads an address inside a bank directly. The loader stops at the
size in the descriptor, so the tail of a shortened bank is the writable
room. Bank 4's last word is 258 bytes. Retiring it, and stopping at
`0x0807B367`, is 259 bytes: `0x0807B264`–`0x0807B367`. That is the existing
cave, not a separate hole.

Retiring more whole words of bank 4, and writing the new size back into
the descriptor, is the way to get more than 259 bytes:

| Words retired | Room |
|---|---|
| 1 | 259 |
| 2 | 450 |
| 3 | 684 |
| 4 | 971 |
| 6 | 1371 |
| 8 | 1831 |
| 15 | 3425 |
| 16 | 3601 |
| 17 | 3881 |
| 18 | 4059 |
| 19 | 4287 |
| 20 | 4442 |
| 21 | 4605 |

Twenty-one is the current mode: 4,569 bytes, placed at `0x0807A16C`
because the 21-word boundary `0x0807A16A` is not a 4-byte address.
Twenty words leave 4,439 usable bytes after alignment, and the display
text overflowed that by 54. Nineteen words are 33 bytes short of the
4,320-byte image from before that text.

The cut has to land on a word boundary. A mid-word size leaves a partial
bitstream. Each retired word is a factory speech word that no longer
plays. `0x0807B367`–`0x0807C84C` stays untouched.

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

The one-word speech cave passes that test. The mode does not fit in it.
The combined image retires 21 bank-4 words. The word boundary is
`0x0807A16A`, so the 4,569 bytes start at `0x0807A16C` and end at
`0x0807B345`. It also changes the bank-4 size, the channel-callback
branch at `0x080478EA`, the key-note branch at `0x0803AD9E`, the button
edges at `0x0804348C` and `0x080434A4`, and both stack tops.
`placement_ok` accepts those eight ranges. The toggle does not write
SuperFreaker's shift-lock site. A double-tap still sets the stock shift
flag, and the shortcut treats that flag as Shift held. Oct | Mod is
control `0x0401`. The arp enable button is `0x0400`; with Shift it
switches the arpeggiator and the sequencer. Key
index n is delivered by a panel frame and becomes MIDI note n+48
before the key branch.

The unmodified SuperFreaker image boots: Renode 1.17 reached its
`main()` at 6,915,727 instructions. The mode image, built in a temp
file from that payload, also reached `main()` and matched the Python
engine on major, inversion, panic, minor, a minor seventh, latch,
strum, and arp. The downloads were not modified.

The lowered stack was checked against PC-relative loads. The only one
at or above `0x2001FE00` is the startup word at `0x0805F884`, and the
patch writes `0x2001FE00` there and in the vector at `0x0800C000`. The
highest other pool word is `0x2001F230`. Words that merely look like
higher SRAM addresses sit inside instructions and are not pools.
