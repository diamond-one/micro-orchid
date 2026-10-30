ENTRY(orchid_chord)
EXTERN(orchid_key)
EXTERN(orchid_button)
midi_dispatch = 0x08048524;
button_handler = 0x08043224;
panel_send = 0x08021414;
MEMORY {
    /* After 21 retired bank-4 words the boundary is 0x0807A16A, which is
       not an instruction address. The image starts at the next 4-byte
       boundary and ends before the live objects at 0x0807B367. */
    FLASH (rx) : ORIGIN = 0x0807A16C, LENGTH = 0x11FB
    STATE (rw) : ORIGIN = 0x2001FE00, LENGTH = 0x100
    MAIL (rw) : ORIGIN = 0x2001FF00, LENGTH = 0x4
}
SECTIONS {
    .text : { *(.text*) *(.rodata*) } > FLASH
    .bss : { *(.bss*) } > STATE
    .mailbox (NOLOAD) : { KEEP(*(.mailbox)) } > MAIL
    /DISCARD/ : { *(.ARM.exidx*) *(.ARM.attributes) *(.comment) *(.note*) }
}
