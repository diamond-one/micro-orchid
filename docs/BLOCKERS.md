# Blockers

## Stock firmware image — booted, not stored here

The user's stock file matches 5.0.0.2084. Container sha256
`c2b405e3c8565b7b73b4dd06522559458190082a8ba633cc5f1bcc43dc64332c`,
payload sha256
`54be2e0b695e2279602513e1a9ed39906408ba221a45e782b61273f0ef55d15f`.
It stays in Downloads. It is not copied into this repo. Renode 1.17 booted
it to `main()`. SuperFreaker 0.1.2 booted the same way. See
`docs/ENVIRONMENT.md`.

## Assembler — the mode is assembled

clang 23.1.4 targets `thumbv7em-none-eabi`. There is no
`arm-none-eabi-gcc`. The mode image is 3,828 bytes. The one-word triad
hook is still 110 bytes and is not what the boot script writes.

## Code space — the speech tail is the room

There is no unused hole in the SuperFreaker image. Spans a reachability
walk does not enter still disassemble as code. The writable room is the
tail of speech bank 4, after its size in the descriptor at `0x08078838`
is shortened to a word boundary.

Retiring the last word frees the existing cave:

- `0x0807B264` .. `0x0807B367` (259 bytes)

That range is byte-identical on stock and SuperFreaker 0.1.2. The mode
does not fit there. A 3,330-byte sketch looked as if fifteen words
(3,425 bytes) would do. The real `-Oz -flto` engine is 3,828 bytes.
Sixteen words free 3,601 and do not fit. Seventeen words free 3,881:
the code occupies `0x0807A440`–`0x0807B334` and 51 bytes remain. See
`docs/SUPERFREAKER.md`.

## Keyboard events in the emulator — blocked

`microfreak-emu` does not run the keyboard coprocessor. `mfemu panel` can
press Shift (`0x0804`) over the documented USART2 frame. It has no id for
OCT | MOD and no id for the 25 keys. Those ids will not be invented.

## Physical flash — not authorized

No device write, erase, factory reset, or recovery drill is allowed by the
mission. M9 stays pending.
