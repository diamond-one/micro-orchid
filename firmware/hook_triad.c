/* One MIDI note-on or note-off becomes a major triad.

   Called instead of the single bl to midi_dispatch in the channel
   callback. The same registers and the same two stack arguments are
   forwarded. Notes that would pass 127 are dropped, which is what
   spell() does. */

typedef unsigned u32;

extern void midi_dispatch(void *state, u32 msg, u32 port, u32 a3, u32 a4, u32 a5);

void orchid_chord(void *state, u32 msg, u32 port, u32 a3, u32 a4, u32 a5) {
    u32 kind = msg & 0xF0u;
    if (kind == 0x80u || kind == 0x90u) {
        u32 note = (msg >> 8) & 0xFFu;
        /* 0, then 4, then 7. Packed so the intervals stay in the instruction
           stream instead of a separate table. */
        u32 intervals = 0x00070400u;
        u32 i;
        for (i = 0; i < 3u; i++) {
            u32 add = (intervals >> (i * 8u)) & 0xFFu;
            u32 n = note + add;
            if (n <= 127u) {
                midi_dispatch(state, (msg & 0xFFFF00FFu) | (n << 8), port, a3, a4, a5);
            }
        }
        return;
    }
    midi_dispatch(state, msg, port, a3, a4, a5);
}
