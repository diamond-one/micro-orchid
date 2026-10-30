# Decisions

## A root alone plays a major triad

The Orchid plays a single note until a quality key is held. This project
plays a major triad instead. The mission requires one root key to produce a
complete chord, and it asks for an explicit default. Major is that default.
Hold a quality key, or latch one, to play anything else.

## Quality conflicts

Suspended plus major, minor, or diminished becomes augmented, minor-add4, or
a power chord. Those interval sets are the published Orchid combinations.
If two of major, minor, and diminished are held, the one pressed later wins.
Extensions stack. Both sevenths can be held together. A ninth is always a
major ninth.

## Four voices

Internal spelling keeps at most four notes. The perfect fifth is dropped
first, which is why C9 is C E Bb D, Cmaj9 is C E B D, and Cm9 is C Eb Bb D.
`voice_limit=None` keeps every tone for an external synth. Several held
roots share the four voices. Newer roots keep a voice when there are more
roots than voices. A pitch used by two chords stays on until the last chord
releases it.

## Inversion, latch, strum, arp

Inversion up or down steps a rotation and leaves it there. The key does not
have to stay down. Latch freezes the quality and extension keys that are
held when it engages. While latched, pressing those keys updates the frozen
set. Strum and arp toggle on the press. Arp replaces a block chord with one
note at a time. Strum delays later note-ons; a root release cancels the ones
that have not sounded.

## Keyboard map

Left 12 keys are modifiers, right 13 are the chromatic roots C through C.
That is a layout decision, not a measurement of the MicroFreak scan codes.
The virtual host treats incoming MIDI as key indexes only after subtracting
`input_base`. The default base, 48, is a test convention.

## Orchid on and off

Shift plus OCT | MOD toggles the host. The combination fires once per press.
Held through power-on, it does not enable the mode. OCT | MOD alone and
Shift alone do not toggle it. Turning the mode off releases every note the
engine generated and clears latch, inversion, strum, and arp. Nothing is
written to flash.

## Coexistence with SuperFreaker 0.1.2

The base image for a combined build is SuperFreaker, not stock. Orchid may
change a byte only when that byte is still equal to stock and
`firmware.coexist.placement_ok` accepts the range. The SuperFreaker banner
and its Shift lock stay. Coprocessor images stay equal to stock, which they
already are in SuperFreaker 0.1.2.

## Placement

There is no erased hole in the SuperFreaker image. Orchid code goes in the
tail of speech bank 4, after that bank's size at `0x08078838` is shortened
to a word boundary. The owner accepted the first cut on 2026-10-30:
retire the 22nd word of bank 4, the words library, and use the 259 bytes
at `0x0807B264`–`0x0807B367`. That held the 110-byte major-triad hook.
The rest of the mode does not fit in one word. The compiled engine is
3,828 bytes, so the image retires the last 17 words of bank 4 and keeps
the first five (size `0x39A`, code `0x0807A440`–`0x0807B334`). Sixteen
words are 227 bytes short. Colors, numbers, letters, and the four
musical voices stay. `0x0807B367`–`0x0807C84C` is not placed in. A span
the reachability walk did not enter is not placed in either. A word is
removed only when the hook is written into that tail. The downloaded
speech files stay unmodified.

## What was not copied

ChoralRoot's engine was read. Its C was not imported. The interval numbers
and the key-mode table are reimplemented in `src/orchid/chords.py`. This
repository does not become GPL-3 because of that reading.
