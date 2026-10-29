# Blockers

## Stock firmware image — blocked

`firmware/stock/` is empty. The emulator cannot boot, and no patch can be
built, until an official MicroFreak 5.0.0.2084 `.mff` is placed there.
Downloading a firmware image from an unofficial source is out of bounds.

## Renode, uv, and an ARM toolchain — blocked

`uv` and Renode are not installed. There is no `gcc`, `clang`, or
`arm-none-eabi-gcc`. A native patch cannot be assembled or executed here.

## Code space — blocked, with a documented reason

`microfreak-tools` `patching.py` at the pinned commit says the 5.0.0.2084
image has no free flash. The cave it uses is the tail of the speech
vocabulary:

- `0x0807B264` .. `0x0807B367` (259 bytes)

That figure is the tool's claim. It has not been re-measured on an image
this repo possesses. 259 bytes cannot hold the chord engine in
`src/orchid/engine.py`. A native port needs a different cave, found by
disassembly of the real image, or a much smaller hook that calls into a
region the image actually has free. Neither has been established.

## Keyboard events in the emulator — blocked

`microfreak-emu` does not run the keyboard coprocessor. `mfemu panel` can
press Shift (`0x0804`) over the documented USART2 frame. It has no id for
OCT | MOD and no id for the 25 keys. Those ids will not be invented.

## Physical flash — not authorized

No device write, erase, factory reset, or recovery drill is allowed by the
mission. M9 stays pending.
