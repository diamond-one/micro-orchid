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
`arm-none-eabi-gcc`. The mode image is 4,545 bytes. The one-word triad
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
words free 4,059. Nineteen words free 4,287 and are 33 bytes short.
Twenty words free 4,442, and after alignment that is 4,439. The display
text overflowed that by 54 bytes. Twenty-one words free 4,605. The
boundary `0x0807A16A` is not 4-byte aligned, so the code is 4,545 bytes
at `0x0807A16C`–`0x0807B32D`.
See `docs/SUPERFREAKER.md`.

## Keyboard events in the emulator — Oct | Mod is 0x0401

`microfreak-emu` does not run the keyboard coprocessor. The main chip
already decodes an 8-byte USART2 frame: `AA`, then six bytes, then an
8-bit sum. A key down is subcommand `0x05` and a key up is `0x06`. The
key index is the low id byte. Stock firmware sounds index n as MIDI note
n+48. That was checked for indexes 0, 7, 12 and 24 (notes 48, 55, 60
and 72). The mode's keyboard entry is the note call at `0x0803AD9E`.
It stays a single stock note until mailbox op 7 arms the layout.

`mfemu panel` knows Shift (`0x0804`) and Hold (`0x0204`). Control
`0x0401` is Arp/Range. The button handler sends that id to the range
editor, and to the sequencer mod-track path when `0x0803B7C0` returns
nonzero. The manual's Oct | Mod button is the control that does those
two jobs: it changes arp range, and it selects a seq mod track. The
image branches at the button down and up calls (`0x0804348C` and
`0x080434A4`). Shift plus that button toggles the layout and does not
run the stock action. The button alone still does. The shortcut sends
`ORCHID ON` and `ORCHID OFF` through the frame builder at `0x080226D0`.
Renode reconstructed both strings. The button alone does not draw them.

## Physical flash — not authorized

No device write, erase, factory reset, or recovery drill is allowed by the
mission. M9 stays pending.
