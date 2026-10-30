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
does not fit there. It retires 17 words of bank 4 and links at
`0x0807A440`. See `docs/BLOCKERS.md`.

`scripts/boot_triad.py` already shows one root, modifiers, latch, strum,
and arp through the firmware note path. Shift+OCT|MOD waits on the
OCT | MOD control id. The bootloader recovery chord is not a test we
are allowed to weaken.

Panel frames that are already documented, and only these, may be reused:
USART2, 8 bytes, `AA` plus six payload bytes plus an 8-bit sum. Button down
from chip `0x20` is `20 01 id_hi id_lo 00 00`. Shift's id in the emulator's
panel table is `0x0804`. Key numbers and OCT | MOD are not in that table.
