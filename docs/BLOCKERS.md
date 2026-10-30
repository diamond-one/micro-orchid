# Blockers

## Stock firmware image — identified, not booted

The user's stock file matches 5.0.0.2084. Container sha256
`c2b405e3c8565b7b73b4dd06522559458190082a8ba633cc5f1bcc43dc64332c`,
payload sha256
`54be2e0b695e2279602513e1a9ed39906408ba221a45e782b61273f0ef55d15f`.
It stays in Downloads. It is not copied into this repo. The emulator has
not booted it.

## Renode, uv, and an ARM toolchain — blocked

`uv` and Renode are not installed. There is no `gcc`, `clang`, or
`arm-none-eabi-gcc`. A native patch cannot be assembled or executed here.

## Code space — blocked, with a documented reason

`microfreak-tools` `patching.py` at the pinned commit says the 5.0.0.2084
image has no free flash. The cave it uses is the tail of the speech
vocabulary:

- `0x0807B264` .. `0x0807B367` (259 bytes)

On the stock image and on SuperFreaker 0.1.2 that cave is byte-identical,
and SuperFreaker did not change the word-bank table. 259 bytes still cannot
hold the chord engine. Runs of zero bytes that are also identical in both
images are inside data tables or misaligned, so they are not a code cave.
See `docs/SUPERFREAKER.md`.

## Keyboard events in the emulator — blocked

`microfreak-emu` does not run the keyboard coprocessor. `mfemu panel` can
press Shift (`0x0804`) over the documented USART2 frame. It has no id for
OCT | MOD and no id for the 25 keys. Those ids will not be invented.

## Physical flash — not authorized

No device write, erase, factory reset, or recovery drill is allowed by the
mission. M9 stays pending.
