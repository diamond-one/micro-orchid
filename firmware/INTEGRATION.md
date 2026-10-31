# Native integration

The mode image is built in a temp file from SuperFreaker 0.1.2. The
downloaded `.mff` files are not modified, and the payload is not stored
in this repo. `scripts/boot_triad.py` is the boot.

A combined build starts from SuperFreaker 0.1.2 and must pass
`firmware.coexist.placement_ok` for every written range. Their banner,
shift-lock handler, and the window at `0x0802B8F0`–`0x0802EF30` stay.
Details and the measured hashes are in `docs/SUPERFREAKER.md`.

The musical rules to port are `src/orchid/chords.py` and the lifecycle in
`src/orchid/engine.py`. A patch is only acceptable when all of the following
are true:

- The input payload sha256 is
  `54be2e0b695e2279602513e1a9ed39906408ba221a45e782b61273f0ef55d15f`
  (473,695 bytes), or every address below has been re-derived for a
  different build.
- The hook address was reached under Renode, not only named from a document.
- The branch is a Thumb-2 branch that preserves registers and the stack.
- The patch stays inside `0x0800C000`–`0x0807FFFF`.
- `firmware/boundaries.py` `PATCH_MANIFEST` lists every changed range.
- `tests` still pass, and an emulator test shows one root event plus the
  selected modifiers producing the expected notes from the firmware process.

`microfreak-tools` documents a 259-byte cave at `0x0807B264`. The mode
does not fit there. It retires 21 words of bank 4 and links at
`0x0807A16C`. The keyboard note call at `0x0803AD9E` is a second branch.
The button edges at `0x0804348C` and `0x080434A4` are a third.
See `docs/BLOCKERS.md`.

`scripts/boot_triad.py` shows one root, modifiers, latch, bass, and arp
through MIDI, then a key root and a minor modifier. Shift plus control
`0x0401` toggles that layout and sends `ORCHID ON` or `ORCHID OFF`
through the frame builder at `0x080226D0`. Shift alone and that button
alone leave a key as one note, and the button alone does not draw those
words. The bootloader recovery chord is not a test we are
allowed to weaken.

Panel frames are USART2, 8 bytes, `AA` plus six payload bytes plus an
8-bit sum. Button down from chip `0x20` is `20 01 id_hi id_lo 00 00`.
Shift's id in the emulator's panel table is `0x0804`. A key down is
`00 05 00 index 00 velocity` and a key up is `00 06 00 index 00 00`.
Index n is MIDI note n+48 on the stock path. Oct | Mod is `0x0401`.
