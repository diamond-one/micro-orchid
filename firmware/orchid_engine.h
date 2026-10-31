/* Orchid performance state. The same file runs in the host tests and in
   the firmware image. Panel scan codes are not in here. */

#ifndef ORCHID_ENGINE_H
#define ORCHID_ENGINE_H

#ifdef ORCHID_EXPORT
#define ORCHID_API __declspec(dllexport)
#else
#define ORCHID_API
#endif

struct orchid_event {
    unsigned char kind; /* 1 note-on, 0 note-off */
    unsigned char note;
    unsigned char velocity;
};

/* voice_limit 0 keeps every tone. The firmware uses 4. */
ORCHID_API void orchid_reset(void);
ORCHID_API void orchid_set_voice_limit(int limit);
/* The first argument is unused. It used to be the strum delay. */
ORCHID_API void orchid_set_timing(int strum_ms, int arp_ms);

ORCHID_API int orchid_modifier(int key, int down, struct orchid_event *out, int cap);
ORCHID_API int orchid_root(int key, int note, int velocity, int on, struct orchid_event *out, int cap);
ORCHID_API int orchid_latch(int enabled, struct orchid_event *out, int cap);
ORCHID_API int orchid_key_mode(int mode, int tonic, struct orchid_event *out, int cap);
ORCHID_API int orchid_advance(int ms, struct orchid_event *out, int cap);
ORCHID_API int orchid_panic(struct orchid_event *out, int cap);
/* Keyboard performance. Off, a key is one stock note. On, indexes 0-11
   are modifiers and 12-24 are roots. Turning it off releases sounding notes. */
ORCHID_API int orchid_arm(int on, struct orchid_event *out, int cap);
ORCHID_API int orchid_held(unsigned char *notes, int cap);

/* Test mailbox. op is applied on the next orchid_service call.
   1 modifier down, 2 modifier up, 3 latch, 4 key mode, 5 advance, 6 panic,
   7 arm the keyboard layout (a = 1 on, 0 off). */
ORCHID_API void orchid_command(int op, int a, int b);
ORCHID_API int orchid_service(struct orchid_event *out, int cap);

#endif
