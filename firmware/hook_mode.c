/* MIDI entry. One note is one root. The keyboard entry is orchid_key:
   stock plays key index n as MIDI note n+48, measured for 0, 7, 12 and 24.
   Armed, notes 48-59 are modifiers and 60-72 are roots. */

#include "orchid_engine.h"

extern void midi_dispatch(void *state, unsigned msg, unsigned port,
                          unsigned a3, unsigned a4, unsigned a5);
extern void button_handler(void *obj, unsigned down, unsigned id, unsigned value);
/* Copies the two words as a 6-byte body and calls the frame builder at
   0x080226D0, then queues the frame on the panel bus. */
extern void panel_send(void *bus, unsigned lo, unsigned hi, unsigned force);
extern int orchid_keyboard_on(void);

/* Same bus object the stock UI passes into the sender. */
#define PANEL_BUS ((void *)0x200005A0)

static const char TEXT_ON[] = "ORCHID ON";
static const char TEXT_OFF[] = "ORCHID OFF";

/* 0x0401 is Arp/Range. The button handler takes that id to the range editor,
   or to the sequencer-mod path when the sequencer is running. The manual's
   Oct | Mod button is the control that does those two jobs. */
#define OCT_MOD_ID 0x0401u
#define SHIFT_ID 0x0804u

static void *voice_state;
static unsigned voice_port;
static unsigned stock_notes;
static unsigned char shift_down;
static unsigned char oct_down;
static unsigned char combo_used;
static unsigned char swallow_up;
static unsigned hook_magic;

/* This RAM is the old stack, not stock BSS. A reset does not clear it.
   The first call zeros the button and voice statics. */
static void ensure_hooks(void) {
    if (hook_magic == 0x4F524348u) return;
    voice_state = 0;
    voice_port = 0;
    stock_notes = 0;
    shift_down = 0;
    oct_down = 0;
    combo_used = 0;
    swallow_up = 0;
    hook_magic = 0x4F524348u;
}

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

static void emit(unsigned status, unsigned note, unsigned velocity) {
    unsigned packed;
    if (!voice_state) return;
    packed = status | (note << 8) | (velocity << 16);
    midi_dispatch(voice_state, packed, voice_port, 0, 0, 0);
}

static void remember_stock(unsigned msg) {
    unsigned kind = msg & 0xF0u;
    unsigned note = (msg >> 8) & 0xFFu;
    unsigned velocity = (msg >> 16) & 0xFFu;
    unsigned bit;
    if (note < 48u || note > 72u) return;
    bit = 1u << (note - 48u);
    if (kind == 0x90u && velocity != 0) stock_notes |= bit;
    else stock_notes &= ~bit;
}

static void release_stock(void) {
    unsigned mask = stock_notes;
    unsigned note = 48u;
    stock_notes = 0;
    while (mask) {
        if (mask & 1u) emit(0x80u, note, 0x40u);
        mask >>= 1;
        note++;
    }
}

/* Body layout the panel already uses: F7, opcode, then up to four
   characters. 0x70 opens a region, 0x72 carries four characters, and
   0x71 carries a shorter tail. */
static void panel_chunk(unsigned opcode, const char *bytes, unsigned count) {
    unsigned lo = 0xF7u | (opcode << 8);
    unsigned hi = 0;
    if (count > 0) lo |= (unsigned)(unsigned char)bytes[0] << 16;
    if (count > 1) lo |= (unsigned)(unsigned char)bytes[1] << 24;
    if (count > 2) hi |= (unsigned char)bytes[2];
    if (count > 3) hi |= (unsigned)(unsigned char)bytes[3] << 8;
    panel_send(PANEL_BUS, lo, hi, 1);
}

static void panel_text(const char *text) {
    unsigned length = 0;
    unsigned index = 0;
    while (text[length] != 0) length++;
    panel_chunk(0x70u, text, 0);
    while (index < length) {
        unsigned chunk = length - index;
        unsigned opcode = chunk >= 4u ? 0x72u : 0x71u;
        if (chunk > 4u) chunk = 4u;
        panel_chunk(opcode, text + index, chunk);
        index += chunk;
    }
}

static void toggle_mode(void) {
    struct orchid_event events[24];
    int count;
    int i;
    if (orchid_keyboard_on()) {
        count = orchid_arm(0, events, 24);
        for (i = 0; i < count; i++) {
            unsigned status = events[i].kind ? 0x90u : 0x80u;
            emit(status, events[i].note, events[i].velocity);
        }
        panel_text(TEXT_OFF);
        return;
    }
    release_stock();
    orchid_arm(1, events, 24);
    panel_text(TEXT_ON);
}

static void handle(void *state, unsigned msg, unsigned port, unsigned a3, unsigned a4, unsigned a5,
                   int keyboard) {
    struct orchid_event events[24];
    unsigned kind = msg & 0xF0u;
    unsigned note = (msg >> 8) & 0xFFu;
    unsigned velocity = (msg >> 16) & 0xFFu;
    int on = kind == 0x90u && velocity != 0;
    int count;
    ensure_hooks();
    voice_state = state;
    voice_port = port;
    count = orchid_service(events, 24);
    play(state, msg, port, a3, a4, a5, events, count);
    if (keyboard && !orchid_keyboard_on()) {
        remember_stock(msg);
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

/* Both button edges arrive here. Shift+Oct|Mod toggles once per press and
   does not run the stock range or mod-track action. Oct|Mod alone still does. */
__attribute__((used))
void orchid_button(void *obj, unsigned down, unsigned id, unsigned value) {
    ensure_hooks();
    if (id == SHIFT_ID) {
        shift_down = down ? 1 : 0;
        if (shift_down && oct_down && !combo_used) {
            combo_used = 1;
            toggle_mode();
        } else if (!(shift_down && oct_down)) {
            combo_used = 0;
        }
        button_handler(obj, down, id, value);
        return;
    }
    if (id == OCT_MOD_ID) {
        oct_down = down ? 1 : 0;
        if (shift_down && oct_down && !combo_used) {
            combo_used = 1;
            swallow_up = 1;
            toggle_mode();
            return;
        }
        if (!(shift_down && oct_down)) combo_used = 0;
        /* The down that toggled was not given to stock. A repeat down
           while Shift stays held must not be given to stock either, or
           the range path sees a down whose up we then swallow. */
        if (swallow_up) {
            if (!down) swallow_up = 0;
            return;
        }
    }
    button_handler(obj, down, id, value);
}
