/* MIDI entry. One note is one root. Modifiers arrive through the
   mailbox until a keyboard trace gives real key ids. */

#include "orchid_engine.h"

extern void midi_dispatch(void *state, unsigned msg, unsigned port,
                          unsigned a3, unsigned a4, unsigned a5);

static void play(void *state, unsigned msg, unsigned port, unsigned a3, unsigned a4, unsigned a5,
                 struct orchid_event *events, int count) {
    unsigned channel = msg & 0x0Fu;
    int i;
    for (i = 0; i < count; i++) {
        unsigned status = (events[i].kind ? 0x90u : 0x80u) | channel;
        unsigned packed = status | ((unsigned)events[i].note << 8) | ((unsigned)events[i].velocity << 16);
        midi_dispatch(state, packed, port, a3, a4, a5);
    }
}

void orchid_chord(void *state, unsigned msg, unsigned port, unsigned a3, unsigned a4, unsigned a5) {
    struct orchid_event events[24];
    unsigned kind = msg & 0xF0u;
    int count = orchid_service(events, 24);
    play(state, msg, port, a3, a4, a5, events, count);
    if (kind == 0x80u || kind == 0x90u) {
        unsigned note = (msg >> 8) & 0xFFu;
        unsigned velocity = (msg >> 16) & 0xFFu;
        int on = kind == 0x90u && velocity != 0;
        count = orchid_root((int)note, (int)note, on ? (int)velocity : 64, on, events, 24);
        play(state, msg, port, a3, a4, a5, events, count);
        return;
    }
    midi_dispatch(state, msg, port, a3, a4, a5);
}
