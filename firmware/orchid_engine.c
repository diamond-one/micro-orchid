#include "orchid_engine.h"

enum {
    Q_DIM = 1, Q_MIN = 2, Q_MAJ = 3, Q_SUS = 4,
    Q_AUG = 5, Q_POW = 6, Q_MIN4 = 7
};
enum { E_6 = 1, E_M7 = 2, E_MAJ7 = 4, E_9 = 8 };

#define MAX_ROOTS 13
#define MAX_TONES 8
#define MAX_HELD 16
#define MAX_STACK 4

static const unsigned char QUALITY[][4] = {
    {0, 0, 0, 0},
    {0, 3, 6, 0},
    {0, 3, 7, 0},
    {0, 4, 7, 0},
    {0, 5, 7, 0},
    {0, 4, 8, 0},
    {0, 7, 12, 0},
    {0, 3, 5, 0},
};
static const unsigned char QUALITY_N[] = {0, 3, 3, 3, 3, 3, 3, 3};
static const unsigned char KEY_MAJOR[12] = {3, 12, 2, 12, 2, 3, 20, 3, 12, 2, 12, 1};
static const unsigned char KEY_MINOR[12] = {2, 12, 1, 3, 12, 2, 12, 2, 3, 20, 3, 12};

static struct {
    unsigned char voice_limit;
    unsigned char sixth_up;
    unsigned char strum;
    unsigned char arp;
    unsigned char latch;
    unsigned char key_mode;
    unsigned char tonic;
    signed char inversion;
    unsigned short strum_ms;
    unsigned short arp_ms;
    unsigned char q_stack[MAX_STACK];
    unsigned char q_n;
    unsigned char ext;
    unsigned char latch_q[MAX_STACK];
    unsigned char latch_n;
    unsigned char latch_ext;
    unsigned char root_key[MAX_ROOTS];
    unsigned char root_note[MAX_ROOTS];
    unsigned char root_vel[MAX_ROOTS];
    unsigned char root_n;
    unsigned char sounding[MAX_HELD];
    unsigned char sound_n;
    unsigned char pend_note[MAX_HELD];
    unsigned char pend_vel[MAX_HELD];
    unsigned int pend_due[MAX_HELD];
    unsigned char pend_n;
    unsigned char arp_pos;
    unsigned int arp_acc;
    unsigned int now;
    unsigned char sig[MAX_HELD];
    unsigned char sig_n;
    unsigned int magic;
} S;

/* Four bytes the emulator writes: op, a, b, ready. The device linker
   pins this at 0x2001FF00. The host test leaves it in ordinary RAM. */
#if defined(ORCHID_DEVICE)
__attribute__((section(".mailbox")))
#endif
ORCHID_API volatile unsigned char orchid_mail[4];

static void zero(void *memory, unsigned count) {
    unsigned char *bytes = memory;
    while (count--) {
        *bytes++ = 0;
    }
}

static void push_event(struct orchid_event *out, int cap, int *count, int kind, int note, int velocity) {
    if (*count < cap && out) {
        out[*count].kind = (unsigned char)kind;
        out[*count].note = (unsigned char)note;
        out[*count].velocity = (unsigned char)velocity;
    }
    (*count)++;
}

static int find_root(int key) {
    int i;
    for (i = 0; i < S.root_n; i++) {
        if (S.root_key[i] == (unsigned char)key) {
            return i;
        }
    }
    return -1;
}

static void remove_root_at(int index) {
    int i;
    for (i = index; i < S.root_n - 1; i++) {
        S.root_key[i] = S.root_key[i + 1];
        S.root_note[i] = S.root_note[i + 1];
        S.root_vel[i] = S.root_vel[i + 1];
    }
    S.root_n--;
}

static unsigned char resolve_quality(const unsigned char *stack, int count) {
    int i, triads = 0, sus = 0;
    unsigned char last = Q_MAJ;
    if (!count) {
        return Q_MAJ;
    }
    for (i = 0; i < count; i++) {
        if (stack[i] == Q_SUS) {
            sus = 1;
        }
        if (stack[i] == Q_DIM || stack[i] == Q_MIN || stack[i] == Q_MAJ) {
            last = stack[i];
            triads++;
        }
    }
    if (sus && triads) {
        if (last == Q_MAJ) return Q_AUG;
        if (last == Q_MIN) return Q_MIN4;
        return Q_POW;
    }
    if (sus) {
        return Q_SUS;
    }
    return last;
}

static int spell(int root, int quality, int ext, int inversion, int limit, unsigned char *out) {
    unsigned char interval[MAX_TONES];
    unsigned char score[MAX_TONES];
    int count = 0, i, j;
    if (root < 0 || root > 127 || limit == 0) {
        return 0;
    }
    for (i = 0; i < QUALITY_N[quality]; i++) {
        int iv = QUALITY[quality][i];
        int sc = iv == 0 ? 100 : (iv == 7 && quality != Q_POW ? 20 : 90);
        int k;
        for (k = 0; k < count; k++) {
            if (interval[k] == iv) {
                if (sc > score[k]) score[k] = (unsigned char)sc;
                break;
            }
        }
        if (k == count && count < MAX_TONES) {
            interval[count] = (unsigned char)iv;
            score[count++] = (unsigned char)sc;
        }
    }
    {
        int extra[4];
        int nextra = 0;
        if (ext & E_6) {
            extra[nextra++] = (S.sixth_up && (ext & (E_M7 | E_MAJ7))) ? 21 : 9;
        }
        if (ext & E_M7) extra[nextra++] = 10;
        if (ext & E_MAJ7) extra[nextra++] = 11;
        if (ext & E_9) extra[nextra++] = 14;
        for (i = 0; i < nextra; i++) {
            int iv = extra[i];
            int sc = iv == 9 || iv == 21 ? 55 : (iv == 14 ? 65 : 75);
            int k;
            for (k = 0; k < count; k++) {
                if (interval[k] == iv) {
                    if (sc > score[k]) score[k] = (unsigned char)sc;
                    break;
                }
            }
            if (k == count && count < MAX_TONES) {
                interval[count] = (unsigned char)iv;
                score[count++] = (unsigned char)sc;
            }
        }
    }
    if (limit < 255 && count > limit) {
        for (i = 0; i < limit; i++) {
            int best = i;
            for (j = i + 1; j < count; j++) {
                if (score[j] > score[best] || (score[j] == score[best] && interval[j] < interval[best])) {
                    best = j;
                }
            }
            {
                unsigned char ti = interval[i], ts = score[i];
                interval[i] = interval[best];
                score[i] = score[best];
                interval[best] = ti;
                score[best] = ts;
            }
        }
        count = limit;
    }
    {
        unsigned char notes[MAX_TONES];
        int n = 0;
        for (i = 0; i < count; i++) {
            int tone = root + interval[i];
            if (tone >= 0 && tone <= 127) {
                notes[n++] = (unsigned char)tone;
            }
        }
        for (i = 0; i < n; i++) {
            for (j = i + 1; j < n; j++) {
                if (notes[j] < notes[i]) {
                    unsigned char tmp = notes[i];
                    notes[i] = notes[j];
                    notes[j] = tmp;
                }
            }
        }
        if (inversion > 0) {
            for (i = 0; i < inversion && n; i++) {
                if (notes[0] + 12 > 127) break;
                notes[0] = (unsigned char)(notes[0] + 12);
                for (j = 0; j < n - 1 && notes[j] > notes[j + 1]; j++) {
                    unsigned char tmp = notes[j];
                    notes[j] = notes[j + 1];
                    notes[j + 1] = tmp;
                }
            }
        } else if (inversion < 0) {
            for (i = 0; i > inversion && n; i--) {
                if (notes[n - 1] < 12) break;
                notes[n - 1] = (unsigned char)(notes[n - 1] - 12);
                for (j = n - 1; j > 0 && notes[j] < notes[j - 1]; j--) {
                    unsigned char tmp = notes[j];
                    notes[j] = notes[j - 1];
                    notes[j - 1] = tmp;
                }
            }
        }
        for (i = 0; i < n; i++) out[i] = notes[i];
        return n;
    }
}

static void fingers(unsigned char *stack, unsigned char *count, unsigned char *ext) {
    int i;
    if (!S.latch) {
        for (i = 0; i < S.q_n; i++) stack[i] = S.q_stack[i];
        *count = S.q_n;
        *ext = S.ext;
        return;
    }
    if (S.q_n || S.ext) {
        for (i = 0; i < S.q_n; i++) S.latch_q[i] = S.q_stack[i];
        S.latch_n = S.q_n;
        S.latch_ext = S.ext;
    }
    for (i = 0; i < S.latch_n; i++) stack[i] = S.latch_q[i];
    *count = S.latch_n;
    *ext = S.latch_ext;
}

static int chord_of(int index, int limit, unsigned char *out) {
    int note = S.root_note[index];
    unsigned char stack[MAX_STACK];
    unsigned char count = 0, ext = 0, quality;
    int shift = 0;
    int sounded;
    fingers(stack, &count, &ext);
    if (count) {
        quality = resolve_quality(stack, count);
    } else if (S.key_mode) {
        const unsigned char *table = S.key_mode == 1 ? KEY_MAJOR : KEY_MINOR;
        unsigned char cell = table[(note + 12 - (S.tonic % 12)) % 12];
        quality = (unsigned char)(cell & 7);
        shift = (cell & 16) ? 1 : ((cell & 8) ? -1 : 0);
    } else {
        quality = Q_MAJ;
    }
    sounded = note + shift;
    if (sounded < 0 || sounded > 127 || limit == 0) {
        return 0;
    }
    return spell(sounded, quality, ext, S.inversion, limit == 255 ? 255 : limit, out);
}

static void budgets(unsigned char *budget) {
    int i, count = S.root_n, limit = S.voice_limit;
    for (i = 0; i < count; i++) budget[i] = 0;
    if (!count) return;
    if (!limit) {
        for (i = 0; i < count; i++) budget[i] = 255;
        return;
    }
    if (count > limit) {
        for (i = count - limit; i < count; i++) budget[i] = 1;
        return;
    }
    {
        int base = limit / count;
        int extra = limit % count;
        for (i = 0; i < count; i++) budget[i] = (unsigned char)base;
        for (i = count - 1; extra > 0 && i >= 0; i--) {
            budget[i]++;
            extra--;
        }
    }
}

static int pool_of(unsigned char notes[][MAX_TONES], const unsigned char *ncount, unsigned char *pool) {
    int i, j, n = 0;
    for (i = 0; i < S.root_n; i++) {
        for (j = 0; j < ncount[i]; j++) {
            int k;
            for (k = 0; k < n; k++) if (pool[k] == notes[i][j]) break;
            if (k == n && n < MAX_HELD) pool[n++] = notes[i][j];
        }
    }
    return n;
}

static int reconcile(struct orchid_event *out, int cap) {
    unsigned char budget[MAX_ROOTS];
    unsigned char notes[MAX_ROOTS][MAX_TONES];
    unsigned char ncount[MAX_ROOTS];
    unsigned char pool[MAX_HELD];
    unsigned char wanted[MAX_HELD];
    unsigned char wvel[MAX_HELD];
    int wn = 0, pool_n, i, j, count = 0;
    int changed;
    budgets(budget);
    for (i = 0; i < S.root_n; i++) {
        ncount[i] = (unsigned char)chord_of(i, budget[i], notes[i]);
    }
    pool_n = pool_of(notes, ncount, pool);
    changed = pool_n != S.sig_n;
    if (!changed) {
        for (i = 0; i < pool_n; i++) if (pool[i] != S.sig[i]) changed = 1;
    }
    if (changed) {
        S.arp_pos = 0;
        S.arp_acc = 0;
        S.pend_n = 0;
        S.sig_n = (unsigned char)pool_n;
        for (i = 0; i < pool_n; i++) S.sig[i] = pool[i];
    }
    if (S.arp && pool_n) {
        int velocity = 1;
        for (i = 0; i < S.root_n; i++) if (S.root_vel[i] > velocity) velocity = S.root_vel[i];
        wanted[0] = pool[S.arp_pos % pool_n];
        wvel[0] = (unsigned char)velocity;
        wn = 1;
    } else {
        for (i = 0; i < S.root_n; i++) {
            for (j = 0; j < ncount[i]; j++) {
                int k;
                for (k = 0; k < wn; k++) if (wanted[k] == notes[i][j]) break;
                if (k < wn) wvel[k] = S.root_vel[i];
                else if (wn < MAX_HELD) {
                    wanted[wn] = notes[i][j];
                    wvel[wn] = S.root_vel[i];
                    wn++;
                }
            }
        }
    }
    if (!changed) {
        int w = 0;
        for (i = 0; i < S.pend_n; i++) {
            for (j = 0; j < wn; j++) if (wanted[j] == S.pend_note[i]) break;
            if (j == wn) continue;
            S.pend_note[w] = S.pend_note[i];
            S.pend_vel[w] = S.pend_vel[i];
            S.pend_due[w] = S.pend_due[i];
            w++;
        }
        S.pend_n = (unsigned char)w;
    }
    {
        unsigned char sorted[MAX_HELD];
        int sn = S.sound_n;
        for (i = 0; i < sn; i++) sorted[i] = S.sounding[i];
        for (i = 0; i < sn; i++) {
            for (j = i + 1; j < sn; j++) {
                if (sorted[j] < sorted[i]) {
                    unsigned char tmp = sorted[i];
                    sorted[i] = sorted[j];
                    sorted[j] = tmp;
                }
            }
        }
        for (i = 0; i < sn; i++) {
            for (j = 0; j < wn; j++) if (wanted[j] == sorted[i]) break;
            if (j != wn) continue;
            push_event(out, cap, &count, 0, sorted[i], 0);
            for (j = 0; j < S.sound_n; j++) {
                if (S.sounding[j] == sorted[i]) {
                    S.sounding[j] = S.sounding[--S.sound_n];
                    break;
                }
            }
        }
    }
    {
        unsigned char fresh[MAX_HELD];
        unsigned char fvel[MAX_HELD];
        int fn = 0;
        for (i = 0; i < wn; i++) {
            for (j = 0; j < S.sound_n; j++) if (S.sounding[j] == wanted[i]) break;
            if (j != S.sound_n) continue;
            for (j = 0; j < S.pend_n; j++) if (S.pend_note[j] == wanted[i]) break;
            if (j != S.pend_n) continue;
            fresh[fn] = wanted[i];
            fvel[fn] = wvel[i];
            fn++;
        }
        for (i = 0; i < fn; i++) {
            for (j = i + 1; j < fn; j++) {
                if (fresh[j] < fresh[i]) {
                    unsigned char tn = fresh[i], tv = fvel[i];
                    fresh[i] = fresh[j];
                    fvel[i] = fvel[j];
                    fresh[j] = tn;
                    fvel[j] = tv;
                }
            }
        }
        if (S.strum && !S.arp) {
            for (i = 0; i < fn; i++) {
                unsigned delay = (unsigned)i * S.strum_ms;
                if (delay == 0) {
                    if (S.sound_n < MAX_HELD) {
                        push_event(out, cap, &count, 1, fresh[i], fvel[i]);
                        S.sounding[S.sound_n++] = fresh[i];
                    }
                } else if (S.pend_n < MAX_HELD) {
                    S.pend_note[S.pend_n] = fresh[i];
                    S.pend_vel[S.pend_n] = fvel[i];
                    S.pend_due[S.pend_n] = S.now + delay;
                    S.pend_n++;
                }
            }
        } else {
            for (i = 0; i < fn; i++) {
                if (S.sound_n < MAX_HELD) {
                    push_event(out, cap, &count, 1, fresh[i], fvel[i]);
                    S.sounding[S.sound_n++] = fresh[i];
                }
            }
        }
    }
    return count;
}

ORCHID_API void orchid_reset(void) {
    zero(&S, sizeof S);
    S.voice_limit = 4;
    S.strum_ms = 30;
    S.arp_ms = 120;
    S.magic = 0x4F524348;
}

ORCHID_API void orchid_set_voice_limit(int limit) {
    if (S.magic != 0x4F524348) orchid_reset();
    S.voice_limit = (unsigned char)(limit < 0 ? 0 : limit);
}

ORCHID_API void orchid_set_timing(int strum_ms, int arp_ms) {
    if (S.magic != 0x4F524348) orchid_reset();
    S.strum_ms = (unsigned short)strum_ms;
    S.arp_ms = (unsigned short)arp_ms;
}

static int ensure(void) {
    if (S.magic != 0x4F524348) orchid_reset();
    return 0;
}

ORCHID_API int orchid_modifier(int key, int down, struct orchid_event *out, int cap) {
    ensure();
    if (key < 0 || key > 11) return 0;
    if (down) {
        if (key < 4) {
            int i;
            for (i = 0; i < S.q_n; i++) if (S.q_stack[i] == (unsigned char)(key + 1)) break;
            if (i == S.q_n && S.q_n < MAX_STACK) S.q_stack[S.q_n++] = (unsigned char)(key + 1);
        } else if (key < 8) {
            S.ext = (unsigned char)(S.ext | (1u << (key - 4)));
        } else if (key == 8) {
            if (S.inversion > -12) S.inversion--;
        } else if (key == 9) {
            if (S.inversion < 12) S.inversion++;
        } else if (key == 10) {
            S.strum ^= 1;
        } else {
            S.arp ^= 1;
            S.arp_pos = 0;
            S.arp_acc = 0;
        }
        return reconcile(out, cap);
    }
    if (key < 4) {
        int i, w = 0;
        for (i = 0; i < S.q_n; i++) {
            if (S.q_stack[i] != (unsigned char)(key + 1)) S.q_stack[w++] = S.q_stack[i];
        }
        S.q_n = (unsigned char)w;
        return reconcile(out, cap);
    }
    if (key < 8) {
        S.ext = (unsigned char)(S.ext & ~(1u << (key - 4)));
        return reconcile(out, cap);
    }
    return 0;
}

static int root_up(int key, struct orchid_event *out, int cap) {
    int index = find_root(key);
    if (index < 0) return 0;
    remove_root_at(index);
    return reconcile(out, cap);
}

ORCHID_API int orchid_root(int key, int note, int velocity, int on, struct orchid_event *out, int cap) {
    int count;
    ensure();
    if (!on) return root_up(key, out, cap);
    if (note < 0 || note > 127) return 0;
    if (velocity < 1) velocity = 1;
    if (velocity > 127) velocity = 127;
    count = 0;
    if (find_root(key) >= 0) count = root_up(key, out, cap);
    if (S.root_n < MAX_ROOTS) {
        S.root_key[S.root_n] = (unsigned char)key;
        S.root_note[S.root_n] = (unsigned char)note;
        S.root_vel[S.root_n] = (unsigned char)velocity;
        S.root_n++;
    }
    return count + reconcile(out + (count < cap ? count : cap), cap - (count < cap ? count : 0));
}

ORCHID_API int orchid_latch(int enabled, struct orchid_event *out, int cap) {
    int i;
    ensure();
    S.latch = enabled ? 1 : 0;
    if (enabled) {
        for (i = 0; i < S.q_n; i++) S.latch_q[i] = S.q_stack[i];
        S.latch_n = S.q_n;
        S.latch_ext = S.ext;
    }
    return reconcile(out, cap);
}

ORCHID_API int orchid_key_mode(int mode, int tonic, struct orchid_event *out, int cap) {
    ensure();
    S.key_mode = (unsigned char)(mode < 0 ? 0 : mode);
    S.tonic = (unsigned char)(tonic & 15);
    return reconcile(out, cap);
}

static int arp_pool_live(void) {
    unsigned char budget[MAX_ROOTS];
    unsigned char notes[MAX_ROOTS][MAX_TONES];
    unsigned char ncount[MAX_ROOTS];
    unsigned char pool[MAX_HELD];
    int i;
    budgets(budget);
    for (i = 0; i < S.root_n; i++) ncount[i] = (unsigned char)chord_of(i, budget[i], notes[i]);
    return pool_of(notes, ncount, pool) > 0;
}

ORCHID_API int orchid_advance(int ms, struct orchid_event *out, int cap) {
    int i, w = 0, count = 0;
    ensure();
    if (ms < 0) return 0;
    S.now += (unsigned)ms;
    if (S.arp && arp_pool_live()) {
        int stepped = 0;
        S.arp_acc += (unsigned)ms;
        while (S.arp_acc >= S.arp_ms) {
            S.arp_acc -= S.arp_ms;
            S.arp_pos++;
            stepped = 1;
        }
        if (stepped) return reconcile(out, cap);
        return 0;
    }
    for (i = 0; i < S.pend_n; i++) {
        int wanted = 0, j;
        /* A due strum note plays only while reconcile still wants it.
           Recompute by seeing it survive in the pending list, which
           reconcile already filtered. */
        if (S.pend_due[i] <= S.now) {
            for (j = 0; j < S.sound_n; j++) if (S.sounding[j] == S.pend_note[i]) break;
            if (j == S.sound_n && S.sound_n < MAX_HELD) {
                push_event(out, cap, &count, 1, S.pend_note[i], S.pend_vel[i]);
                S.sounding[S.sound_n++] = S.pend_note[i];
            }
            (void)wanted;
        } else {
            S.pend_note[w] = S.pend_note[i];
            S.pend_vel[w] = S.pend_vel[i];
            S.pend_due[w] = S.pend_due[i];
            w++;
        }
    }
    S.pend_n = (unsigned char)w;
    return count;
}

ORCHID_API int orchid_panic(struct orchid_event *out, int cap) {
    unsigned char sorted[MAX_HELD];
    int i, j, count = 0, sn;
    ensure();
    sn = S.sound_n;
    for (i = 0; i < sn; i++) sorted[i] = S.sounding[i];
    for (i = 0; i < sn; i++) {
        for (j = i + 1; j < sn; j++) {
            if (sorted[j] < sorted[i]) {
                unsigned char tmp = sorted[i];
                sorted[i] = sorted[j];
                sorted[j] = tmp;
            }
        }
    }
    for (i = 0; i < sn; i++) push_event(out, cap, &count, 0, sorted[i], 0);
    {
        unsigned short strum_ms = S.strum_ms, arp_ms = S.arp_ms;
        unsigned char limit = S.voice_limit;
        zero(&S, sizeof S);
        S.voice_limit = limit;
        S.strum_ms = strum_ms;
        S.arp_ms = arp_ms;
        S.magic = 0x4F524348;
    }
    return count;
}

ORCHID_API int orchid_held(unsigned char *notes, int cap) {
    unsigned char sorted[MAX_HELD];
    int i, j, n;
    ensure();
    n = S.sound_n;
    for (i = 0; i < n; i++) sorted[i] = S.sounding[i];
    for (i = 0; i < n; i++) {
        for (j = i + 1; j < n; j++) {
            if (sorted[j] < sorted[i]) {
                unsigned char tmp = sorted[i];
                sorted[i] = sorted[j];
                sorted[j] = tmp;
            }
        }
    }
    if (n > cap) n = cap;
    for (i = 0; i < n; i++) notes[i] = sorted[i];
    return S.sound_n;
}

ORCHID_API int orchid_pending_count(void) {
    ensure();
    return S.pend_n;
}

ORCHID_API void orchid_command(int op, int a, int b) {
    ensure();
    orchid_mail[0] = (unsigned char)op;
    orchid_mail[1] = (unsigned char)a;
    orchid_mail[2] = (unsigned char)b;
    orchid_mail[3] = 1;
}

ORCHID_API int orchid_service(struct orchid_event *out, int cap) {
    unsigned char op, a, b;
    if (S.magic != 0x4F524348) {
        orchid_reset();
        orchid_mail[0] = 0;
        orchid_mail[1] = 0;
        orchid_mail[2] = 0;
        orchid_mail[3] = 0;
    }
    if (!orchid_mail[3]) return 0;
    op = orchid_mail[0];
    a = orchid_mail[1];
    b = orchid_mail[2];
    orchid_mail[3] = 0;
    if (op == 1) return orchid_modifier(a, 1, out, cap);
    if (op == 2) return orchid_modifier(a, 0, out, cap);
    if (op == 3) return orchid_latch(a, out, cap);
    if (op == 4) return orchid_key_mode(a, b, out, cap);
    if (op == 5) return orchid_advance(a | (b << 8), out, cap);
    if (op == 6) return orchid_panic(out, cap);
    return 0;
}
