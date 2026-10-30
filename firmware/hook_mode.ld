ENTRY(orchid_chord)
EXTERN(orchid_key)
midi_dispatch = 0x08048524;
MEMORY {
    /* Bank 4 word boundary after 18 retired words. Ends before the live
       objects at 0x0807B367. */
    FLASH (rx) : ORIGIN = 0x0807A38C, LENGTH = 0xFDB
    STATE (rw) : ORIGIN = 0x2001FE00, LENGTH = 0x100
    MAIL (rw) : ORIGIN = 0x2001FF00, LENGTH = 0x4
}
SECTIONS {
    .text : { *(.text*) *(.rodata*) } > FLASH
    .bss : { *(.bss*) } > STATE
    .mailbox (NOLOAD) : { KEEP(*(.mailbox)) } > MAIL
    /DISCARD/ : { *(.ARM.exidx*) *(.ARM.attributes) *(.comment) *(.note*) }
}
