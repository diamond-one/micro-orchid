# Progress

Phase: Orchid Mode is in a SuperFreaker image. Under Renode the MIDI path
matched the Python engine for a major triad, an inversion, panic, a minor
triad, a minor seventh, latch, strum, and arp. The same image also
branches at the key-note call. Key index n is MIDI note n+48. Mailbox
op 7 still arms the same layout. Shift plus control `0x0401` toggles it.
That id is Arp/Range, which is also the sequencer mod-track button.
The same shortcut sends `ORCHID ON` and `ORCHID OFF` through the panel
frame builder. Renode reconstructed both strings.

## Done

- Read `instructions.txt`.
- Confirmed this repo had no earlier plan, safety notes, or firmware.
- Cloned microfreak-emu `9f80bc3`, microfreak-tools `396fcf4`, and
  ChoralRoot `bd7f431` under `third_party/` (gitignored).
- Implemented `src/orchid/chords.py`, `engine.py`, `layout.py`, `midi_host.py`.
- Ported that engine to `firmware/orchid_engine.c`. The host DLL matches
  the Python cases. The device build is the same source with
  `-DORCHID_DEVICE`.
- The patch manifest lists the mode image's eight ranges. No firmware bytes.
- Verified the stock `.mff` container and payload hashes.
- Diffed SuperFreaker 0.1.2: 5,705 bytes, main image only. Recorded the
  ranges in `firmware/superfreaker_v0_1_2_ranges.json`. Coprocessors match
  stock. The speech cave is untouched by SuperFreaker. Their shift-lock
  site is reserved.
- Measured the mode at 4,493 bytes with `-Oz -flto`. Twenty-one bank-4
  words leave 4,605 bytes. The boundary is `0x0807A16A`, so the code
  starts at the next 4-byte address (`0x0807A16C`) and ends at
  `0x0807B2F9`. Twenty leave 4,439 usable bytes and were 54 short once
  the display text was added. The image keeps the first word of that
  bank. Colors, numbers, letters, and the four musical voices stay.
- Measured the key frame on stock firmware under Renode. Subcommand
  `0x05` is key down, `0x06` is key up, and index n sounds as note n+48.

## Not done

- A stored Orchid image. The booted payload is a temp file. The downloads
  were not modified. A temp hash is not a release candidate.

## Latest test

`python -m unittest discover -s tests` and `python scripts/boot_triad.py`

- unit tests: PASS (69 ran, 0 failed, 0 errors)
- stock firmware boot: PASS (`main()` at 6,915,574 instructions, PC `0x08023444`)
- SuperFreaker 0.1.2 boot: PASS (`main()` at 6,915,727 instructions, PC `0x08024FB6`)
- mode image: PASS. Reached `main()`. Against the Python engine: note 60
  played 60, 64, 67; inversion up released 60 and played 72; panic released
  64, 67, 72; minor played 60, 63, 67; a minor seventh added 70; latch kept
  minor after the key lift and returned to major when latch cleared; strum
  played 60, then 64, and a root release cancelled the rest; arp played 60
  and the next step released 60 and played 64. Key 12 then played 60, 64,
  67; key 1 moved 64 to 63; releasing key 12 cleared the chord. After
  disarm, key 12 played only 60. Shift alone and Oct|Mod alone left that
  key as one note. Shift then Oct|Mod released the held note, and the
  next press played 60, 64, 67. The same shortcut again released that
  chord, and the next press was one note. The arm step's display frames
  reconstructed as `ORCHID ON`. The disarm step reconstructed as
  `ORCHID OFF`. Oct|Mod alone did not draw either string.
- placement review: the only PC-relative SRAM load at or above `0x2001FE00`
  is the startup stack word at `0x0805F884`, which the patch updates with
  the vector. The next-highest pool word is `0x2001F230`. `placement_ok`
  accepts the eight ranges.
- hardware flash: NOT RUN

## Next

The display text is in the temp image. A second person has not reviewed
the eight ranges. Do not write an image to a device, and do not treat
the temp payload as a release candidate.
