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
`arm-none-eabi-gcc`. The mode image is 3,924 bytes. The one-word triad
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
(3,425 bytes) would do. The engine before the keyboard entry was 3,828
bytes. Sixteen words free 3,601 and do not fit. Seventeen words free
3,881 and were 45 bytes short once the keyboard entry was added. Eighteen
words free 4,059: the code is 3,924 bytes at `0x0807A38C`–`0x0807B2E0`.
See `docs/SUPERFREAKER.md`.

## Keyboard events in the emulator — keys measured, OCT | MOD not

`microfreak-emu` does not run the keyboard coprocessor. The main chip
already decodes an 8-byte USART2 frame: `AA`, then six bytes, then an
8-bit sum. A key down is subcommand `0x05` and a key up is `0x06`. The
key index is the low id byte. Stock firmware sounds index n as MIDI note
n+48. That was checked for indexes 0, 7, 12 and 24 (notes 48, 55, 60
and 72). The mode's keyboard entry is the note call at `0x0803AD9E`.
It stays a single stock note until mailbox op 7 arms the layout.

`mfemu panel` knows Shift (`0x0804`) and Hold (`0x0204`). Pressing the
button ids the handler compares did not put OCT or MOD on the display.
`0x0401` showed a Range screen, `0x0405` Time Division, `0x0503` LFO
Sync, and `0x0902` a matrix assign. None of those is named OCT | MOD
here. That id is still unknown, and the Shift+OCT|MOD toggle is not in
the image.

## Physical flash — not authorized

No device write, erase, factory reset, or recovery drill is allowed by the
mission. M9 stays pending.
