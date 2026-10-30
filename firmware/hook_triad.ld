ENTRY(orchid_chord)
midi_dispatch = 0x08048524;
SECTIONS {
    .text 0x0807B264 : {
        *(.text.orchid_chord)
        *(.text*)
        *(.rodata*)
    }
    /DISCARD/ : { *(.ARM.exidx*) *(.ARM.attributes) *(.comment) *(.note*) }
}
