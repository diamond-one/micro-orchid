ENTRY(orchid_chord)
midi_dispatch = 0x08048524;
MEMORY {
    /* Bank 4 word boundary for 17 retired words, rounded up to a Thumb
       literal alignment. Ends before the live objects at 0x0807B367. */
    FLASH (rx) : ORIGIN = 0x0807A440, LENGTH = 0xF27
    STATE (rw) : ORIGIN = 0x2001FE00, LENGTH = 0x100
    MAIL (rw) : ORIGIN = 0x2001FF00, LENGTH = 0x4
}
SECTIONS {
    .text : { *(.text*) *(.rodata*) } > FLASH
    .bss : { *(.bss*) } > STATE
    .mailbox (NOLOAD) : { KEEP(*(.mailbox)) } > MAIL
    /DISCARD/ : { *(.ARM.exidx*) *(.ARM.attributes) *(.comment) *(.note*) }
}
