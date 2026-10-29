# Native integration

No firmware bytes have been changed.

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

`microfreak-tools` documents a 259-byte cave at `0x0807B264`. That is not
large enough for this engine. See `docs/BLOCKERS.md`.

The first useful emulator test, after a boot of unmodified firmware, is a
single root producing C E G through the firmware's own note path. Modifier
keys come after that. Shift+OCT|MOD comes after the OCT | MOD control id is
known. The bootloader recovery chord is not a test we are allowed to weaken.

Panel frames that are already documented, and only these, may be reused:
USART2, 8 bytes, `AA` plus six payload bytes plus an 8-bit sum. Button down
from chip `0x20` is `20 01 id_hi id_lo 00 00`. Shift's id in the emulator's
panel table is `0x0804`. Key numbers and OCT | MOD are not in that table.
