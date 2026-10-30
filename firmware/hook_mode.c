/* MIDI entry. One note is one root. The keyboard entry is orchid_key:
   stock plays key index n as MIDI note n+48, measured for 0, 7, 12 and 24.
   Armed, notes 48-59 are modifiers and 60-72 are roots. */

#include "orchid_engine.h"

extern void midi_dispatch(void *state, unsigned msg, unsigned port,
                          unsigned a3, unsigned a4, unsigned a5);
extern int orchid_keyboard_on(void);

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

static void handle(void *state, unsigned msg, unsigned port, unsigned a3, unsigned a4, unsigned a5,
                   int keyboard) {
    struct orchid_event events[24];
    unsigned kind = msg & 0xF0u;
    unsigned note = (msg >> 8) & 0xFFu;
    unsigned velocity = (msg >> 16) & 0xFFu;
    int on = kind == 0x90u && velocity != 0;
    int count = orchid_service(events, 24);
    play(state, msg, port, a3, a4, a5, events, count);
    if (keyboard && !orchid_keyboard_on()) {
        midi_dispatch(state, msg, port, a3, a4, a5);
        return;
    }
    if (keyboard && note >= 48u && note <= 59u) {
        count = orchid_modifier((int)(note - 48u), on, events, 24);
        play(state, msg, port, a3, a4, a5, events, count);
        return;
    }
    if (kind == 0x80u || kind == 0x90u) {
        if (!keyboard || (note >= 60u && note <= 72u)) {
            count = orchid_root((int)note, (int)note, on ? (int)velocity : 64, on, events, 24);
            play(state, msg, port, a3, a4, a5, events, count);
            return;
        }
    }
    midi_dispatch(state, msg, port, a3, a4, a5);
}

void orchid_chord(void *state, unsigned msg, unsigned port, unsigned a3, unsigned a4, unsigned a5) {
    handle(state, msg, port, a3, a4, a5, 0);
}

__attribute__((used))
void orchid_key(void *state, unsigned msg, unsigned port, unsigned a3, unsigned a4, unsigned a5) {
    handle(state, msg, port, a3, a4, a5, 1);
}
