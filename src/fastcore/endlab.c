/* endlab — exhaustive jump-timing search of the 8-4 final room on the QuickNES core (N1).
 *
 *   endlab CORE ROM INPUTS.bin [--input-skip 2] [edits] MODE...
 *
 * Input edits (applied to the movie before anything runs; frames are core frames of the
 * ORIGINAL movie, applied in the order given):
 *   --set F=PAD      replace the pad on core frame F
 *   --insert F=PAD   insert one new frame with PAD before core frame F (everything after shifts +1)
 *   --delete F       delete core frame F (everything after shifts -1)
 *
 * Modes:
 *   --replay              run the whole (edited) movie; print victory frame and last non-zero input
 *   --trace A B           print per-frame state for core frames A..B of the (edited) movie
 *   --bfs F0 F1           breadth-first search over every jump timing from core frame F0 to F1.
 *        Alphabet: --pads P1,P2,... (default 0x82,0x83 = B+R and A+B+R: cap speed is kept, the only
 *        choice per frame is whether A is down).  States are deduplicated on the gameplay RAM, so
 *        the search is exhaustive over that alphabet.  A node is restored as (one full savestate
 *        per frame) + (its own 2 KB of RAM)  [F50].
 *        --coast A B      for frames t in A..B, test every airborne node of frame t with NO INPUT
 *                         from t on: if the axe is reached, last input = t-1.  Stops at the first t
 *                         that has a success (prints up to --show of them).
 *        --out FILE       write the best movie (edited prefix + path + zeros) in INPUTS.bin format
 *        --maxnodes N     abort if a frontier exceeds N (default 400000)
 *        --ground-at F    at the start of frame F keep only the nodes standing on the ground
 *        --pick N         with --ground-at: write the movie reaching grounded node N (then B+R
 *                         filler) to --out and stop.  Used to hand a room's first half to a second
 *                         run that searches the ending from a single node.
 *        --allow-stomp    keep Hammer Bro stomp branches (dropped by default: each stomp frame
 *                         forks the world and multiplies the frontier)
 *        --no-xprune      keep nodes that fell behind the furthest x (dropped by default: at cap
 *                         speed a node that bumped terrain can never catch up)
 *        --diag           print grounded-node and distinct-enemy-world counts with the progress
 *      So the search is exhaustive over jump timings for lines that keep full speed; it says
 *      nothing about lines that give up position.
 *   --speedup F0 T        N2: structured no-L+R speed-up plans from core F0, best x at core T
 *   --accel F0 T          N2: Pareto search over every no-L+R pad from core F0, best x at core T
 *   --pokescan T ADDR LO HI STEP
 *                         N3: poke one RAM byte after core frame T (LO = -1: no poke) and print the
 *                         frame StarFlagTaskControl ($0746) first becomes non-zero and the next load
 *   --flag F0 F1          N3: every input from core F0 at a flagpole; goal = $0746 non-zero within 6
 *        frames of a grab (the 8-2 style ending).  Dedup per frame on the player's physical state.
 *        --xmin X         drop nodes left of x pixel X
 *        --walk N         for grabs up to core N, follow the automatic walk and tally the castle frame
 *        --pads P1,P2,... restrict the search to these pads (e.g. 0x82,0x83 = full speed, jump timing only)
 *        --fullfrom F     with --pads: every pad again from core F on
 *        --airfull        --pads restricts floor frames only; in the air every pad is tried
 *        --clip           air pads: Right or a Left tap while moving direction is right; coast or Left after it
 *        --through X Y    wall-clip probe: report the first node whose left side point is inside a non-empty
 *                         tile at speed >= 20, and the first node with x >= X and y >= Y; paths go to --out.embed/.through
 *        --fully Y        with --fullfrom: entering core F keep only on-screen nodes with y >= Y
 *        --xline X T      drop nodes that cannot have x pixel >= X on core T at the 2.5 px/frame cap
 *                         (admissible when every wanted grab needs x >= X no later than core T)
 *   --turn F0 D           N4: every no-L+R input from core F0; goal = vertical pipe entry with
 *        ScreenLeft >= --slmin (3345) on a frame <= D.  Nodes that cannot reach x pixel --xgoal
 *        (3404) by D at 1.79 units/frame of leftward acceleration are dropped (admissible).
 *        --beam K         keep the K best nodes per physical bucket (heuristic; 0 = every node)
 *
 * Pad encoding (same as harness/ram_oracle): A 01, B 02, SEL 04, START 08, U 10, D 20, L 40, R 80.
 * Victory = OperMode ($0770) == 2 with WorldNumber ($075F) >= 7.  Death = GES ($0e) 11 or 6, or
 * Player_Y_HighPos ($b5) > 1.
 */
#include <dlfcn.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <libretro.h>

static uint8_t cur_pad;
static bool env_cb(unsigned cmd, void *data) {
    switch (cmd) {
    case RETRO_ENVIRONMENT_SET_PIXEL_FORMAT: return true;
    case RETRO_ENVIRONMENT_GET_CAN_DUPE: *(bool *)data = true; return true;
    case RETRO_ENVIRONMENT_GET_SYSTEM_DIRECTORY:
    case RETRO_ENVIRONMENT_GET_SAVE_DIRECTORY: *(const char **)data = "."; return true;
    case RETRO_ENVIRONMENT_GET_VARIABLE: {
        struct retro_variable *v = (struct retro_variable *)data;
        if (!strcmp(v->key, "quicknes_up_down_allowed")) { v->value = "enabled"; return true; }
        if (!strcmp(v->key, "quicknes_no_sprite_limit")) { v->value = "disabled"; return true; }
        return false; }
    case RETRO_ENVIRONMENT_GET_VARIABLE_UPDATE: *(bool *)data = false; return true;
    case RETRO_ENVIRONMENT_SET_MEMORY_MAPS:
    case RETRO_ENVIRONMENT_SET_INPUT_DESCRIPTORS:
    case RETRO_ENVIRONMENT_SET_CONTROLLER_INFO:
    case RETRO_ENVIRONMENT_SET_GEOMETRY: return true;
    default: return false;
    }
}
static void video_cb(const void *d, unsigned w, unsigned h, size_t p) { (void)d; (void)w; (void)h; (void)p; }
static void audio_cb(int16_t l, int16_t r) { (void)l; (void)r; }
static size_t audio_batch_cb(const int16_t *d, size_t n) { (void)d; return n; }
static void input_poll_cb(void) {}
static int16_t input_state_cb(unsigned port, unsigned dev, unsigned idx, unsigned id) {
    (void)idx;
    if (port != 0 || (dev & 0xff) != RETRO_DEVICE_JOYPAD) return 0;
    uint8_t p = cur_pad;
    static const int map[9] = { 0x02, 0, 0x04, 0x08, 0x10, 0x20, 0x40, 0x80, 0x01 }; /* B Y SEL START U D L R A */
    if (id == RETRO_DEVICE_ID_JOYPAD_MASK) {
        int16_t m = 0;
        for (int i = 0; i < 9; i++) if (map[i] && (p & map[i])) m |= 1 << i;
        return m;
    }
    return id < 9 && map[id] && (p & map[id]) ? 1 : 0;
}
#define SYM(name) name##_t name = (name##_t)dlsym(h, #name); if (!name) { fprintf(stderr, "missing %s\n", #name); return 1; }
typedef void (*retro_set_environment_t)(retro_environment_t);
typedef void (*retro_set_video_refresh_t)(retro_video_refresh_t);
typedef void (*retro_set_audio_sample_t)(retro_audio_sample_t);
typedef void (*retro_set_audio_sample_batch_t)(retro_audio_sample_batch_t);
typedef void (*retro_set_input_poll_t)(retro_input_poll_t);
typedef void (*retro_set_input_state_t)(retro_input_state_t);
typedef void (*retro_init_t)(void);
typedef void (*retro_deinit_t)(void);
typedef bool (*retro_load_game_t)(const struct retro_game_info *);
typedef void (*retro_unload_game_t)(void);
typedef void (*retro_run_t)(void);
typedef size_t (*retro_serialize_size_t)(void);
typedef bool (*retro_serialize_t)(void *, size_t);
typedef bool (*retro_unserialize_t)(const void *, size_t);
typedef void *(*retro_get_memory_data_t)(unsigned);
typedef size_t (*retro_get_memory_size_t)(unsigned);

static double now(void) { struct timespec t; clock_gettime(CLOCK_MONOTONIC, &t); return t.tv_sec + t.tv_nsec * 1e-9; }

#define RAMSZ 0x800
static uint64_t fnv_add(uint64_t h, const uint8_t *p, size_t n) {
    for (size_t i = 0; i < n; i++) { h ^= p[i]; h *= 1099511628211ULL; }
    return h;
}
/* Gameplay key: object state in the zero page, sub-pixels/forces, Bowser vars, collision bits,
 * frenzy/range cells, player physics vars, timers.  Cosmetic and sound state is left out, and the
 * player's vertical sub-pixel residue is ignored while he stands (InitJS zeroes it at take-off). */
static uint64_t state_key(const uint8_t *r) {
    uint64_t h = 1469598103934665603ULL;
    uint8_t t[0x50];
    h = fnv_add(h, r + 0x09, 0xea - 0x09 + 1);
    memcpy(t, r + 0x400, 0x50);
    if (r[0x1d] == 0) t[0x16] = 0;
    h = fnv_add(h, t, 0x50);
    h = fnv_add(h, r + 0x363, 8);
    h = fnv_add(h, r + 0x490, 0x10);
    h = fnv_add(h, r + 0x6ae, 0x19);         /* $06ae-$06c6 hammer offsets, misc collision flags */
    h = fnv_add(h, r + 0x6cb, 0x09);         /* $06cb-$06d3 frenzy buffer/queue, duplicate offset */
    h = fnv_add(h, r + 0x6d6, 0x09);         /* $06d6-$06de (skips ColorRotateOffset, PlayerGfxOffset) */
    memcpy(t, r + 0x700, 0x0c);
    if (r[0x1d] == 0) { t[7] = 0; t[8] = 0; } /* jump origin is dead state while standing */
    h = fnv_add(h, t, 0x0c);
    h = fnv_add(h, r + 0x70e, 0x52);         /* $070e-$075f */
    h = fnv_add(h, r + 0x780, 1);
    h = fnv_add(h, r + 0x783, 0x21);         /* $0783-$07a3 */
    return h;
}

/* Player-physics key for the flagpole search (--flag).  Only what the next frames of player motion
 * read: joypad carry-over (A held), routine, state, directions, speeds, position and sub-pixels,
 * collision bits, the stored running speed and its flag, the friction fraction, jump forces and
 * the running timer.  Standing on the floor (y 176) the vertical residue and the jump forces are
 * dead state, because the only way up from there is InitJS, which rewrites them.  Scroll, timers
 * tied to the frame and everything cosmetic are left out. */
static uint64_t flag_key(const uint8_t *r) {
    uint8_t t[32]; int i = 0, fl = (r[0x1d] == 0 && r[0xce] == 176);
    t[i++] = r[0x0d] & 0x80; t[i++] = r[0x0e]; t[i++] = r[0x1d]; t[i++] = r[0x33]; t[i++] = r[0x45];
    t[i++] = r[0x57]; t[i++] = r[0x6d]; t[i++] = r[0x86]; t[i++] = r[0x9f]; t[i++] = r[0xb5]; t[i++] = r[0xce];
    t[i++] = r[0x400]; t[i++] = fl ? 0 : r[0x416]; t[i++] = r[0x433]; t[i++] = r[0x490];
    t[i++] = r[0x700]; t[i++] = r[0x703]; t[i++] = r[0x705];
    t[i++] = fl ? 0 : r[0x709]; t[i++] = fl ? 0 : r[0x70a]; t[i++] = r[0x783];
    return fnv_add(1469598103934665603ULL, t, (size_t)i);
}

/* --turn --beam K: keep the K best nodes (lowest projected x) in each physical bucket */
typedef struct { uint64_t b; double s; long i; } BeamEnt;
static int cmp_beam(const void *pa, const void *pb) {
    const BeamEnt *a = pa, *b = pb;
    if (a->b != b->b) return a->b < b->b ? -1 : 1;
    if (a->s != b->s) return a->s < b->s ? -1 : 1;
    return a->i < b->i ? -1 : (a->i > b->i);
}

typedef struct { int32_t parent; uint8_t pad; } Meta;
typedef struct { uint64_t *keys; uint32_t cap, n; } Set;
static void set_init(Set *s, uint32_t cap) { s->cap = cap; s->n = 0; s->keys = calloc(cap, sizeof(uint64_t)); }
static int set_add(Set *s, uint64_t k) {   /* returns 1 if newly added */
    if (!k) k = 1;
    uint32_t i = (uint32_t)(k * 11400714819323198485ULL >> 32) & (s->cap - 1);
    while (s->keys[i]) { if (s->keys[i] == k) return 0; i = (i + 1) & (s->cap - 1); }
    s->keys[i] = k; s->n++;
    return 1;
}
static void set_clear(Set *s) { memset(s->keys, 0, (size_t)s->cap * sizeof(uint64_t)); s->n = 0; }

int main(int argc, char **argv) {
    if (argc < 5) { fprintf(stderr, "usage: see header of src/fastcore/endlab.c\n"); return 2; }
    const char *core = argv[1], *rom = argv[2], *inputs = argv[3], *outpath = NULL;
    long input_skip = 0;
    int mode = 0;                       /* 1 replay, 2 trace, 3 bfs */
    long tA = -1, tB = -1, F0 = -1, F1 = -1, cA = -1, cB = -1, maxnodes = 400000, show = 8;
    uint8_t pads[16]; int npads = 0;
    long gnd[8]; int ngnd = 0;          /* --ground-at F: keep only grounded nodes at frame F */
    int allow_stomp = 0; long nstomp = 0; int diag = 0; int xprune = 1; long nxdrop = 0;
    long pick = -1;                     /* --pick N with --ground-at C: write the path to grounded node N and stop */
    long pk_addr = 0, pk_lo = 0, pk_hi = 0, pk_step = 1;   /* --pokescan T ADDR LO HI STEP */
    long xmin = 0;                      /* --flag: drop nodes whose x pixel is left of this */
    long walkto = -1;                   /* --flag --walk N: time the castle walk for grabs up to core N */
    long pickf_y = -1, pickf_t = -1, pickf_xmax = -1;   /* --flag --pickfloor Y F [--pickxmax X] */
    long xmax = -1;                     /* --flag --xmax X: drop nodes right of x pixel X */
    long boxy = -1;                     /* --flag --boxy Y: from --fullfrom on, drop nodes above y pixel Y */
    long clipfrom = -1;                 /* --flag --clipfrom F: the --clip grammar starts on core F (restricted pads before) */
    int clipg = 0;                      /* --flag --clip: air pads follow the wall-entry grammar (see the search loop) */
    int airfull = 0;                    /* --flag --airfull: --pads restricts the floor only; every air pad is tried */
    long thr_x = -1, thr_y = 0;         /* --flag --through X Y: report nodes with x pixel >= X and y >= Y (on screen) */
    long fully = -1;                    /* --flag --fully Y: on the last restricted frame keep only nodes with y >= Y (on screen) */
    long fullfrom = -1;                 /* --flag --fullfrom F: with --pads, use every pad again from core F on */
    long xline_x = -1, xline_t = -1;    /* --flag --xline X T: drop nodes that cannot reach x pixel X by core T at 2.5 px/frame */
    long slmin = 3345, xgoal = 3404;    /* --turn: required ScreenLeft, and the rightmost x pixel that enters the pipe */
    long beam = 0;                      /* --turn --beam K: keep K nodes per physical bucket (0 = exhaustive) */
    int allow_lr = 0;                   /* --turn --lr: also try the Left+Right floor pads (the WR's category) */
    long ptA = -1, ptB = -2;            /* --pokescan --ptrace A B: print the poked run for core frames A..B */
    long p2a[8], p2v[8]; int np2 = 0;   /* --pokescan --poke2 ADDR=VAL: extra fixed pokes applied with the swept one */
    long sw_lo = 0, sw_hi = 0x7ff, sw_limit = 300, ev_addr = 0x746, ev_seen_addr = -1;   /* --ramsweep T LO HI */
    int ev_val = 0, ev_nz = 1, ev_seen_val = 0;
    FILE *f = fopen(inputs, "rb"); if (!f) { perror(inputs); return 1; }
    fseek(f, 0, SEEK_END); long nin = ftell(f); fseek(f, 0, SEEK_SET);
    uint8_t *in = malloc(nin + 4096);
    if (fread(in, 1, nin, f) != (size_t)nin) { perror("read inputs"); return 1; }
    fclose(f);
    memset(in + nin, 0, 4096);
    /* first pass: options that the edits depend on */
    for (int i = 4; i < argc; i++) if (!strcmp(argv[i], "--input-skip")) input_skip = strtol(argv[i + 1], NULL, 0);
    for (int i = 4; i < argc; i++) {
        if (!strcmp(argv[i], "--input-skip")) i++;
        else if (!strcmp(argv[i], "--set")) { char *e; long t = strtol(argv[++i], &e, 0); int v = (*e == '=') ? (int)strtol(e + 1, NULL, 0) : 0;
            fprintf(stderr, "set core %ld: %02x -> %02x\n", t, in[t + input_skip], v); in[t + input_skip] = (uint8_t)v; }
        else if (!strcmp(argv[i], "--insert")) { char *e; long t = strtol(argv[++i], &e, 0); int v = (*e == '=') ? (int)strtol(e + 1, NULL, 0) : 0;
            long k = t + input_skip; memmove(in + k + 1, in + k, nin - k); in[k] = (uint8_t)v; nin++;
            fprintf(stderr, "insert pad %02x before core %ld\n", v, t); }
        else if (!strcmp(argv[i], "--delete")) { long t = strtol(argv[++i], NULL, 0); long k = t + input_skip;
            memmove(in + k, in + k + 1, nin - k - 1); nin--; fprintf(stderr, "delete core %ld\n", t); }
        else if (!strcmp(argv[i], "--replay")) mode = 1;
        else if (!strcmp(argv[i], "--trace")) { mode = 2; tA = strtol(argv[++i], NULL, 0); tB = strtol(argv[++i], NULL, 0); }
        else if (!strcmp(argv[i], "--speedup")) { mode = 4; tA = strtol(argv[++i], NULL, 0); tB = strtol(argv[++i], NULL, 0); }
        else if (!strcmp(argv[i], "--accel")) { mode = 5; tA = strtol(argv[++i], NULL, 0); tB = strtol(argv[++i], NULL, 0); }
        else if (!strcmp(argv[i], "--flag")) { mode = 7; F0 = strtol(argv[++i], NULL, 0); F1 = strtol(argv[++i], NULL, 0); }
        else if (!strcmp(argv[i], "--xmin")) xmin = strtol(argv[++i], NULL, 0);
        else if (!strcmp(argv[i], "--walk")) walkto = strtol(argv[++i], NULL, 0);
        else if (!strcmp(argv[i], "--fullfrom")) fullfrom = strtol(argv[++i], NULL, 0);
        else if (!strcmp(argv[i], "--fully")) fully = strtol(argv[++i], NULL, 0);
        else if (!strcmp(argv[i], "--airfull")) airfull = 1;
        else if (!strcmp(argv[i], "--clip")) clipg = 1;
        else if (!strcmp(argv[i], "--boxy")) boxy = strtol(argv[++i], NULL, 0);
        else if (!strcmp(argv[i], "--xmax")) xmax = strtol(argv[++i], NULL, 0);
        else if (!strcmp(argv[i], "--pickfloor")) { pickf_y = strtol(argv[++i], NULL, 0); pickf_t = strtol(argv[++i], NULL, 0); }
        else if (!strcmp(argv[i], "--pickxmax")) pickf_xmax = strtol(argv[++i], NULL, 0);
        else if (!strcmp(argv[i], "--clipfrom")) clipfrom = strtol(argv[++i], NULL, 0);
        else if (!strcmp(argv[i], "--through")) { thr_x = strtol(argv[++i], NULL, 0); thr_y = strtol(argv[++i], NULL, 0); }
        else if (!strcmp(argv[i], "--xline")) { xline_x = strtol(argv[++i], NULL, 0); xline_t = strtol(argv[++i], NULL, 0); }
        else if (!strcmp(argv[i], "--turn")) { mode = 8; F0 = strtol(argv[++i], NULL, 0); F1 = strtol(argv[++i], NULL, 0); }
        else if (!strcmp(argv[i], "--ramsweep")) { mode = 9; tA = strtol(argv[++i], NULL, 0); sw_lo = strtol(argv[++i], NULL, 0); sw_hi = strtol(argv[++i], NULL, 0); }
        else if (!strcmp(argv[i], "--ev") || !strcmp(argv[i], "--ev-seen")) { int sn = argv[i][4] == '-'; char *eq = strchr(argv[++i], '='); if (!eq) return 2;
            if (sn) { ev_seen_addr = strtol(argv[i], NULL, 0); ev_seen_val = (int)strtol(eq + 1, NULL, 0); }
            else { ev_addr = strtol(argv[i], NULL, 0); ev_val = (int)strtol(eq + 1, NULL, 0); ev_nz = 0; } }
        else if (!strcmp(argv[i], "--ev-nz")) { ev_addr = strtol(argv[++i], NULL, 0); ev_nz = 1; }
        else if (!strcmp(argv[i], "--limit")) sw_limit = strtol(argv[++i], NULL, 0);
        else if (!strcmp(argv[i], "--beam")) beam = strtol(argv[++i], NULL, 0);
        else if (!strcmp(argv[i], "--ptrace")) { ptA = strtol(argv[++i], NULL, 0); ptB = strtol(argv[++i], NULL, 0); }
        else if (!strcmp(argv[i], "--poke2") && np2 < 8) { char *eq = strchr(argv[++i], '='); if (!eq) return 2;
            p2a[np2] = strtol(argv[i], NULL, 0); p2v[np2] = strtol(eq + 1, NULL, 0); np2++; }
        else if (!strcmp(argv[i], "--lr")) allow_lr = 1;
        else if (!strcmp(argv[i], "--slmin")) slmin = strtol(argv[++i], NULL, 0);
        else if (!strcmp(argv[i], "--xgoal")) xgoal = strtol(argv[++i], NULL, 0);
        else if (!strcmp(argv[i], "--pokescan")) { mode = 6; tA = strtol(argv[++i], NULL, 0); pk_addr = strtol(argv[++i], NULL, 0);
            pk_lo = strtol(argv[++i], NULL, 0); pk_hi = strtol(argv[++i], NULL, 0); pk_step = strtol(argv[++i], NULL, 0); }
        else if (!strcmp(argv[i], "--bfs")) { mode = 3; F0 = strtol(argv[++i], NULL, 0); F1 = strtol(argv[++i], NULL, 0); }
        else if (!strcmp(argv[i], "--coast")) { cA = strtol(argv[++i], NULL, 0); cB = strtol(argv[++i], NULL, 0); }
        else if (!strcmp(argv[i], "--out")) outpath = argv[++i];
        else if (!strcmp(argv[i], "--maxnodes")) maxnodes = strtol(argv[++i], NULL, 0);
        else if (!strcmp(argv[i], "--ground-at") && ngnd < 8) gnd[ngnd++] = strtol(argv[++i], NULL, 0);
        else if (!strcmp(argv[i], "--allow-stomp")) allow_stomp = 1;
        else if (!strcmp(argv[i], "--diag")) diag = 1;
        else if (!strcmp(argv[i], "--no-xprune")) xprune = 0;
        else if (!strcmp(argv[i], "--pick")) pick = strtol(argv[++i], NULL, 0);
        else if (!strcmp(argv[i], "--show")) show = strtol(argv[++i], NULL, 0);
        else if (!strcmp(argv[i], "--pads")) { char *dup = strdup(argv[++i]), *tok = strtok(dup, ",");
            while (tok && npads < 16) { pads[npads++] = (uint8_t)strtol(tok, NULL, 0); tok = strtok(NULL, ","); } free(dup); }
        else { fprintf(stderr, "unknown option %s\n", argv[i]); return 2; }
    }
    int padsgiven = npads > 0;          /* --flag: restrict pads only when --pads was passed (bug 2026-11-12..13: the default below restricted it always) */
    if (!npads) { pads[0] = 0x82; pads[1] = 0x83; npads = 2; }
    if (!mode) { fprintf(stderr, "no mode given\n"); return 2; }

    void *h = dlopen(core, RTLD_NOW | RTLD_LOCAL);
    if (!h) { fprintf(stderr, "dlopen: %s\n", dlerror()); return 1; }
    SYM(retro_set_environment) SYM(retro_set_video_refresh) SYM(retro_set_audio_sample)
    SYM(retro_set_audio_sample_batch) SYM(retro_set_input_poll) SYM(retro_set_input_state)
    SYM(retro_init) SYM(retro_deinit) SYM(retro_load_game) SYM(retro_unload_game) SYM(retro_run)
    SYM(retro_serialize_size) SYM(retro_serialize) SYM(retro_unserialize)
    SYM(retro_get_memory_data) SYM(retro_get_memory_size)
    FILE *rf = fopen(rom, "rb"); if (!rf) { perror(rom); return 1; }
    fseek(rf, 0, SEEK_END); long rsz = ftell(rf); fseek(rf, 0, SEEK_SET);
    void *rdata = malloc(rsz);
    if (fread(rdata, 1, rsz, rf) != (size_t)rsz) { perror("rom read"); return 1; }
    fclose(rf);
    retro_set_environment(env_cb);
    retro_set_video_refresh(video_cb); retro_set_audio_sample(audio_cb);
    retro_set_audio_sample_batch(audio_batch_cb);
    retro_set_input_poll(input_poll_cb); retro_set_input_state(input_state_cb);
    retro_init();
    struct retro_game_info gi = { rom, rdata, (size_t)rsz, NULL };
    if (!retro_load_game(&gi)) { fprintf(stderr, "retro_load_game failed\n"); return 1; }
    uint8_t *ram = (uint8_t *)retro_get_memory_data(RETRO_MEMORY_SYSTEM_RAM);
    if (!ram || retro_get_memory_size(RETRO_MEMORY_SYSTEM_RAM) < RAMSZ) { fprintf(stderr, "no system RAM\n"); return 1; }
    size_t ssz = retro_serialize_size();
    long nf = nin - input_skip;
    #define RAMP() (ram = (uint8_t *)retro_get_memory_data(RETRO_MEMORY_SYSTEM_RAM))
    #define DEAD(r) ((r)[0x0e] == 11 || (r)[0x0e] == 6 || (r)[0xb5] > 1)
    #define WON(r)  ((r)[0x770] == 2 && (r)[0x75f] >= 7)

    if (mode == 1) {
        long vic = -1, last = -1, i;
        for (i = 0; i < nf + 400; i++) {
            cur_pad = (i < nf) ? in[i + input_skip] : 0; if (cur_pad) last = i;
            retro_run(); RAMP();
            if (vic < 0 && WON(ram)) { vic = i; break; }
        }
        long lastb = -1; for (long q = 0; q < nf && (vic < 0 || q <= vic); q++) if (in[q + input_skip]) lastb = q;
        printf("replay: victory_core=%ld  last_nonzero_input_core=%ld  (WR: victory 17864, last input 17846)\n", vic, lastb);
        (void)last;
        return 0;
    }
    if (mode == 2) {
        printf("core pad GES st  x      sub y   ysp xsp xmf SL   FC  | slots flag:id:x:y x5 | bowser spd rng tmr | misc states x9 | lfsr0-2\n");
        for (long i = 0; i <= tB; i++) {
            cur_pad = (i < nf) ? in[i + input_skip] : 0; retro_run(); RAMP();
            if (i < tA) continue;
            printf("%ld %02x %2u %u %5u %3u %3u %3d %2u %3u %4u %3u |", i, cur_pad, ram[0x0e], ram[0x1d],
                   ram[0x6d] * 256 + ram[0x86], ram[0x400], ram[0xce], (int8_t)ram[0x9f], ram[0x57], ram[0x705],
                   ram[0x71a] * 256 + ram[0x71c], ram[0x09]);
            for (int q = 0; q < 5; q++) printf(" %02x:%02x:%u:%u", ram[0x0f + q], ram[0x16 + q], ram[0x6e + q] * 256 + ram[0x87 + q], ram[0xcf + q]);
            printf(" | %d %02x %u |", (int8_t)ram[0x365], ram[0x6dc], ram[0x78a + ram[0x368]]);
            for (int q = 0; q < 9; q++) printf(" %02x", ram[0x2a + q]);
            printf(" | %02x %02x %02x", ram[0x7a7], ram[0x7a8], ram[0x7a9]);
            printf("%s%s\n", WON(ram) ? " WON" : "", DEAD(ram) ? " DEAD" : "");
        }
        return 0;
    }

    if (mode == 4) {
        /* N2: structured enumeration of no-Left+Right speed-ups from a standstill at a pipe exit.
         * Plan: p1 (L or L+B) | B (skid-zero, keeps facing left) | jump A+R+B held h, R+B until
         * landed | g ground frames R+B | one-frame L tap | J frames A+R+B (0 = walk off) | R+B.
         * Reports Mario's 24-bit x (1/256 px) at frame T for every plan, best first, against the
         * movie's own inputs. */
        long F0s = tA, T = tB;
        for (long i = 0; i < F0s; i++) { cur_pad = in[i + input_skip]; retro_run(); }
        void *S = malloc(ssz); retro_serialize(S, ssz);
        for (long i = F0s; i <= T; i++) { cur_pad = in[i + input_skip]; retro_run(); }
        RAMP();
        long base = ((long)ram[0x6d] << 16) | ((long)ram[0x86] << 8) | ram[0x400];
        printf("movie: x at core %ld = %ld + %ld/256 (speed %u)\n", T, base >> 8, base & 255, ram[0x57]);
        typedef struct { long x; int p1, h, g, tap, J, spd, capf; } Res;
        Res *res = malloc(sizeof(Res) * 4096); int nres = 0;
        static const uint8_t P1[2] = {0x40, 0x42}, TP[2] = {0x40, 0x42};
        for (int a = 0; a < 2; a++) for (int h = 1; h <= 8; h++) for (int g = 1; g <= 5; g++)
        for (int tp = 0; tp < 2; tp++) for (int J = 0; J <= 3; J++) {
            retro_unserialize(S, ssz); RAMP();
            int phase = 0, cnt = 0, dead = 0, capf = -1;
            for (long i = F0s; i <= T; i++) {
                uint8_t pad = 0x82;
                switch (phase) {
                case 0: pad = P1[a]; break;
                case 1: pad = 0x02; break;
                case 2: pad = (cnt < h) ? 0x83 : 0x82; break;
                case 3: pad = 0x82; break;
                case 4: pad = TP[tp]; break;
                default: pad = (cnt < J) ? 0x83 : 0x82; break;
                }
                cur_pad = pad; retro_run(); RAMP();
                if (DEAD(ram)) { dead = 1; break; }
                if (capf < 0 && ram[0x57] == 40) capf = (int)(i - F0s);
                switch (phase) {
                case 0: phase = 1; break;
                case 1: phase = 2; cnt = 0; break;
                case 2: cnt++; if (cnt >= 2 && ram[0x1d] == 0) { phase = 3; cnt = 0; } break;
                case 3: cnt++; if (cnt >= g) phase = 4; break;
                case 4: phase = 5; cnt = 0; break;
                default: cnt++; break;
                }
            }
            if (dead) continue;
            res[nres].x = ((long)ram[0x6d] << 16) | ((long)ram[0x86] << 8) | ram[0x400];
            res[nres].p1 = P1[a]; res[nres].h = h; res[nres].g = g; res[nres].tap = TP[tp]; res[nres].J = J;
            res[nres].spd = ram[0x57]; res[nres].capf = capf; nres++;
        }
        for (int i = 0; i < nres; i++) for (int j = i + 1; j < nres; j++) if (res[j].x > res[i].x) { Res t = res[i]; res[i] = res[j]; res[j] = t; }
        for (int i = 0; i < nres && i < show; i++)
            printf("x=%ld+%3ld/256  (%+.3f px vs movie)  speed %d  cap after %d frames | p1=%02x hold=%d ground=%d tap=%02x J=%d\n",
                   res[i].x >> 8, res[i].x & 255, (res[i].x - base) / 256.0, res[i].spd, res[i].capf,
                   res[i].p1, res[i].h, res[i].g, res[i].tap, res[i].J);
        return 0;
    }

    if (mode == 6) {
        /* N3: poke one RAM byte right after core frame T and report, for each value, the frame the
         * castle is "entered" (StarFlagTaskControl $0746 first non-zero) and the frame the next
         * area loads (GES $0e back to 0 after the flag sequence).  The movie's own inputs follow. */
        long T = tA;
        for (long i = 0; i <= T; i++) { cur_pad = in[i + input_skip]; retro_run(); }
        RAMP();
        void *S = malloc(ssz); retro_serialize(S, ssz);
        printf("pokescan after core %ld: addr $%04lx (movie value %u)  ->  value: castle_frame load_frame\n", T, pk_addr, ram[pk_addr]);
        long prevc = -2, prevl = -2;
        for (long v = pk_lo; v <= pk_hi; v += pk_step) {
            retro_unserialize(S, ssz); RAMP();
            if (v >= 0) ram[pk_addr] = (uint8_t)v;
            for (int q = 0; q < np2; q++) ram[p2a[q]] = (uint8_t)p2v[q];      /* --poke2 ADDR=VAL: fixed extra pokes */
            long cas = -1, ld = -1; int seen5 = ram[0x0e] == 5 || ram[0x0e] == 4;
            for (long i = T + 1; i < T + 1200; i++) {
                cur_pad = (i < nf) ? in[i + input_skip] : 0; retro_run(); RAMP();
                if (i >= ptA && i <= ptB)       /* --ptrace A B: follow the poked run frame by frame */
                    printf("    %ld ges%u st%u x%d.%03d y%u xs%d ys%d mdir%u face%u abs%u run%u xmf%u cbits%02x cst%u\n", i, ram[0x0e], ram[0x1d],
                           (ram[0x6d] << 8) | ram[0x86], ram[0x400] * 1000 / 256, ram[0xce], (int8_t)ram[0x57], (int8_t)ram[0x9f],
                           ram[0x45], ram[0x33], ram[0x700], ram[0x703], ram[0x705], ram[0x490], ram[0x789]);
                if (ram[0x0e] == 5 || ram[0x0e] == 4) seen5 = 1;
                if (cas < 0 && ram[0x746]) cas = i;
                if (seen5 && ram[0x0e] == 0) { ld = i; break; }
                if (DEAD(ram)) break;
            }
            if (cas != prevc || ld != prevl || v == pk_lo) printf("  value %3ld: castle %ld  load %ld\n", v, cas, ld);
            prevc = cas; prevl = ld;
        }
        return 0;
    }

    if (mode == 5) {
        /* N2: Pareto search for the best speed-up from core frame F0 to T with no Left+Right.
         * Every pad without L+R / Up / Down is tried each frame (B is not varied in the air, where
         * it has no effect on x physics).  Nodes are grouped by "mode" (player state, facing and
         * moving direction, the whole vertical state, A held, running flags, collision bits) and
         * within a mode a node is dropped when another one is at least as far right AND at least
         * as fast and within 4 px of it (the 4 px keeps positional variety near ledges).
         * A finder, not a proof: dominance is assumed monotone.  Reports the furthest x at T among
         * nodes at speed 40, against the movie's own x, with the pad sequence. */
        long F0a = tA, T = tB;
        for (long i = 0; i < F0a; i++) { cur_pad = in[i + input_skip]; retro_run(); }
        RAMP();
        long nfa = T - F0a + 1;
        void **tm = calloc(nfa + 2, sizeof(void *)); Meta **mt = calloc(nfa + 2, sizeof(Meta *));
        tm[0] = malloc(ssz); retro_serialize(tm[0], ssz);
        uint8_t *cu = malloc(RAMSZ), *nx = NULL; long nc = 1, capx = 0;
        memcpy(cu, ram, RAMSZ);
        mt[0] = malloc(sizeof(Meta)); mt[0][0].parent = -1; mt[0][0].pad = 0;
        /* movie baseline */
        void *tmpS = malloc(ssz); retro_serialize(tmpS, ssz);
        for (long i = F0a; i <= T; i++) { cur_pad = in[i + input_skip]; retro_run(); }
        RAMP();
        long basex = ((long)ram[0x6d] << 16) | ((long)ram[0x86] << 8) | ram[0x400];
        printf("movie: x at core %ld = %ld+%ld/256 speed %u\n", T, basex >> 8, basex & 255, ram[0x57]);
        typedef struct { uint64_t key; int n; int idx[24]; } Slot;
        uint32_t hcap = 1u << 18; Slot *ht = malloc(sizeof(Slot) * hcap);
        long *nxX = NULL, *nxV = NULL; uint8_t *alive = NULL; double ta = now(); long st = 0;
        static const uint8_t GP[12] = {0x00,0x40,0x80,0x02,0x42,0x82,0x01,0x41,0x81,0x03,0x43,0x83};
        static const uint8_t AP[6]  = {0x02,0x42,0x82,0x03,0x43,0x83};
        for (long k = 0; k < nfa; k++) {
            long maxch = nc * 12 + 16;
            if (maxch > capx) { capx = maxch; nx = realloc(nx, (size_t)capx * RAMSZ); nxX = realloc(nxX, capx * sizeof(long)); nxV = realloc(nxV, capx * sizeof(long)); alive = realloc(alive, capx); }
            mt[k + 1] = malloc((size_t)maxch * sizeof(Meta));
            memset(ht, 0, sizeof(Slot) * hcap);
            long nn = 0;
            for (long n = 0; n < nc; n++) {
                const uint8_t *src = cu + n * RAMSZ;
                int air = src[0x1d] != 0; const uint8_t *PL = air ? AP : GP; int np = air ? 6 : 12;
                for (int p = 0; p < np; p++) {
                    retro_unserialize(tm[k], ssz); RAMP(); memcpy(ram, src, RAMSZ);
                    cur_pad = PL[p]; retro_run(); RAMP(); st++;
                    if (DEAD(ram) || ram[0x0e] != 8) continue;
                    if (!tm[k + 1]) { tm[k + 1] = malloc(ssz); retro_serialize(tm[k + 1], ssz); }
                    long X = ((long)ram[0x6d] << 16) | ((long)ram[0x86] << 8) | ram[0x400];
                    long V = (long)(int8_t)ram[0x57] * 256 + ram[0x705];
                    uint8_t mk[20] = { ram[0x1d], ram[0x33], ram[0x45], ram[0xce], ram[0xb5], ram[0x9f], ram[0x433],
                                       (uint8_t)(ram[0x1d] ? ram[0x416] : 0), ram[0x709], ram[0x70a],
                                       (uint8_t)(ram[0x1d] ? ram[0x708] : 0), (uint8_t)(ram[0x0a] & 0x80), (uint8_t)(ram[0x783] != 0),
                                       (uint8_t)(ram[0x703] != 0), ram[0x490], ram[0x785], ram[0x0e], ram[0x704], ram[0x70e], ram[0x714] };
                    uint64_t key = fnv_add(1469598103934665603ULL, mk, sizeof mk); if (!key) key = 1;
                    uint32_t hi = (uint32_t)(key * 11400714819323198485ULL >> 32) & (hcap - 1);
                    while (ht[hi].key && ht[hi].key != key) hi = (hi + 1) & (hcap - 1);
                    Slot *s = &ht[hi]; s->key = key;
                    int dom = 0;
                    for (int q = 0; q < s->n; q++) { long j = s->idx[q]; if (!alive[j]) continue;
                        if (nxX[j] >= X && nxV[j] >= V && nxX[j] - X <= 1024) { dom = 1; break; } }
                    if (dom) continue;
                    for (int q = 0; q < s->n; q++) { long j = s->idx[q]; if (alive[j] && X >= nxX[j] && V >= nxV[j] && X - nxX[j] <= 1024) alive[j] = 0; }
                    int w = 0; for (int q = 0; q < s->n; q++) if (alive[s->idx[q]]) s->idx[w++] = s->idx[q];
                    s->n = w;
                    if (s->n >= 24) continue;                 /* mode full: keep what is there */
                    memcpy(nx + nn * RAMSZ, ram, RAMSZ); nxX[nn] = X; nxV[nn] = V; alive[nn] = 1;
                    mt[k + 1][nn].parent = (int32_t)n; mt[k + 1][nn].pad = PL[p]; s->idx[s->n++] = (int)nn; nn++;
                }
            }
            long j = 0;                                        /* compact the survivors */
            for (long n = 0; n < nn; n++) if (alive[n]) {
                if (j != n) { memmove(nx + j * RAMSZ, nx + n * RAMSZ, RAMSZ); mt[k + 1][j] = mt[k + 1][n]; nxX[j] = nxX[n]; nxV[j] = nxV[n]; }
                j++; }
            nn = j;
            if (!nn) { printf("frontier empty at core %ld\n", F0a + k); return 1; }
            { uint8_t *sw = cu; cu = nx; nx = sw; } nc = nn;
            nx = realloc(nx, (size_t)capx * RAMSZ);
            if (k % 5 == 4 || k == nfa - 1) { printf("  core %ld: %ld nodes (%.0fs, %ld steps)\n", F0a + k + 1, nc, now() - ta, st); fflush(stdout); }
            if (k == nfa - 1) {
                long best = -1, bx = -1;
                for (long n = 0; n < nc; n++) { const uint8_t *r = cu + n * RAMSZ; if (r[0x57] != 40) continue;
                    long X = ((long)r[0x6d] << 16) | ((long)r[0x86] << 8) | r[0x400]; if (X > bx) { bx = X; best = n; } }
                if (best < 0) { printf("no node at speed 40 by core %ld\n", T); return 1; }
                printf("best: x at core %ld = %ld+%ld/256  (%+.4f px vs movie)\n", T, bx >> 8, bx & 255, (bx - basex) / 256.0);
                uint8_t *path = malloc(nfa + 1); long idx = best;
                for (long q = nfa; q >= 1; q--) { path[q - 1] = mt[q][idx].pad; idx = mt[q][idx].parent; }
                printf("pads from core %ld:", F0a); for (long q = 0; q < nfa; q++) printf(" %02x", path[q]); printf("\n");
                if (outpath) { FILE *o = fopen(outpath, "wb"); fwrite(in, 1, F0a + input_skip, o); fwrite(path, 1, nfa, o);
                    fwrite(in + T + 1 + input_skip, 1, nin - (T + 1 + input_skip), o); fclose(o); printf("wrote %s (movie with the segment replaced)\n", outpath); }
            }
        }
        (void)tmpS;
        return 0;
    }

    if (mode == 7) {
        /* N3/H54: exhaustive local search at a flagpole.  Goal: StarFlagTaskControl ($0746) non-zero
         * within 6 frames of the grab (the 8-2 style ending, no castle walk).  Pads: all of A/B/L/R
         * on the ground; in the air B is not read and L+R acts as L or R alone, so A/L/R while
         * rising and L/R while falling (A held through a fall only blocks the next jump).  Dedup per
         * frame on flag_key.  Every grab is counted with its routine (4 slide, 5 glitch) and height. */
        if (F0 < 0 || F1 <= F0) { fprintf(stderr, "--flag F0 F1 required\n"); return 2; }
        for (long i = 0; i < F0; i++) { cur_pad = in[i + input_skip]; retro_run(); }
        RAMP();
        long nfr = F1 - F0 + 1, ncur = 1, capx = 1 << 12, steps = 0, ndrop = 0, nskip = 0, first5 = -1;
        long g4 = 0, g5 = 0, gy[256]; memset(gy, 0, sizeof gy);
        long gminpx = 1L << 40, gminpx5 = 1L << 40;
        long nemb = 0, nthr = 0; int embbest = 0, embfirst = 0, thrfirst = 0;
        long cas[600]; memset(cas, 0, sizeof cas); long casbest = -1, caslen = 0, casgrab = -1; int casy = 0, casfive = 0; uint8_t *caspath = NULL;
        void **tmpl = calloc(nfr + 2, sizeof(void *)); Meta **meta = calloc(nfr + 2, sizeof(Meta *));
        uint8_t *cur = malloc(RAMSZ), *nxt = malloc((size_t)capx * RAMSZ);
        tmpl[0] = malloc(ssz); if (!retro_serialize(tmpl[0], ssz)) return 1;
        memcpy(cur, ram, RAMSZ);
        meta[0] = malloc(sizeof(Meta)); meta[0][0].parent = -1; meta[0][0].pad = 0;
        Set seen; set_init(&seen, 1u << 24);
        static const uint8_t gp[16] = { 0x00,0x40,0x80,0x01,0x41,0x81,0xc0,0xc1,0x02,0x42,0x82,0xc2,0x03,0x43,0x83,0xc3 };
        double t0 = now();
        printf("flag search %ld..%ld xmin %ld  start x %d y %d xspd %d abs %d  savestate %zu bytes\n", F0, F1, xmin,
               (ram[0x6d] << 8) | ram[0x86], ram[0xce], (int8_t)ram[0x57], ram[0x700], ssz);
        for (long k = 0; k < nfr; k++) {
            long t = F0 + k, nn = 0, capm = ncur * 16 + 1;
            long gmax = -1, gmax25 = -1, hop = -1;      /* diagnostics, x in 1/256 px */
            meta[k + 1] = malloc((size_t)capm * sizeof(Meta)); set_clear(&seen);
            for (long n = 0; n < ncur; n++) {
                const uint8_t *r0 = cur + n * RAMSZ;
                int np = r0[0x1d] == 0 ? 16 : ((int8_t)r0[0x9f] < 0 ? 6 : 3);
                int restricted = padsgiven && (fullfrom < 0 || t < fullfrom);
                if (restricted && airfull && r0[0x1d] != 0) restricted = 0;
                if (restricted) np = npads;
                /* --clip: air grammar for a speed-keeping wall entry.  Moving direction right: Right held or a
                 * Left tap; moving direction left (after the tap): coast or more Left.  A only while rising. */
                static const uint8_t cg_r[4] = { 0x80, 0x40, 0x81, 0x41 }, cg_l[4] = { 0x00, 0x40, 0x01, 0x41 };
                int clipair = clipg && t >= clipfrom && r0[0x1d] != 0;
                if (clipair) np = (int8_t)r0[0x9f] < 0 ? 4 : 2;
                for (int p = 0; p < np; p++) {
                    uint8_t thispad = clipair ? (r0[0x45] == 2 ? cg_l[p] : cg_r[p]) : restricted ? pads[p] : gp[p];
                    retro_unserialize(tmpl[k], ssz); RAMP(); memcpy(ram, r0, RAMSZ);
                    cur_pad = thispad; retro_run(); RAMP(); steps++;
                    if (DEAD(ram)) continue;
                    long x = ((long)ram[0x6d] << 8) | ram[0x86], xf = (x << 8) | ram[0x400];
                    if (x < xmin && (fullfrom < 0 || t >= fullfrom)) { ndrop++; continue; }
                    if (boxy >= 0 && (fullfrom < 0 || t >= fullfrom) && ram[0x0e] == 8 && (ram[0xb5] != 1 || ram[0xce] < boxy)) { ndrop++; continue; }
                    if (xmax >= 0 && x > xmax) { ndrop++; continue; }
                    if (fully >= 0 && t + 1 == fullfrom && ram[0x0e] == 8 && (ram[0xb5] != 1 || ram[0xce] < fully)) { ndrop++; continue; }
                    if (xline_t >= 0 && ram[0x0e] == 8 && (t > xline_t || xf < (xline_x << 8) - 640 * (xline_t - t))) { ndrop++; continue; }
                    if (thr_x >= 0) {       /* wall-clip probes: left side point inside a non-empty tile at speed, and "got through" */
                        int col = (int)((x + 2) >> 4), row = ((int)ram[0xce] + 24 - 32) >> 4, spd = (int8_t)ram[0x57], hit = 0;
                        if (ram[0xb5] == 1 && ram[0xce] + 24 >= 32 && row >= 0 && row < 13 &&
                            ram[0x500 + ((col >> 4) & 1) * 0xd0 + row * 16 + (col & 15)] && spd >= 20) {
                            nemb++; if (spd > embbest) embbest = spd; if (!embfirst) { embfirst = 1; hit = 1; } }
                        if (x >= thr_x && ram[0xb5] == 1 && ram[0xce] >= thr_y) { nthr++; if (!thrfirst) { thrfirst = 1; hit = 2; } }
                        if (hit) {
                            uint8_t *gpath = malloc(k + 2); long gi = n;
                            for (long q = k; q >= 1; q--) { gpath[q - 1] = meta[q][gi].pad; gi = meta[q][gi].parent; }
                            gpath[k] = thispad;
                            printf("  FIRST %s on core %ld: x %.3f y %d xspd %d state %d movingdir %d (probe col %d row %d)\n", hit == 1 ? "EMBEDDED AT SPEED" : "THROUGH", t,
                                   xf / 256.0, ram[0xce], spd, ram[0x1d], ram[0x45], col, row);
                            printf("  last 24 pads:"); for (long q = k > 23 ? k - 23 : 0; q <= k; q++) printf(" %02x", gpath[q]); printf("\n");
                            if (outpath) { char nm[1200]; snprintf(nm, sizeof nm, "%s.%s", outpath, hit == 1 ? "embed" : "through");
                                FILE *o = fopen(nm, "wb"); if (o) { fwrite(in, 1, F0 + input_skip, o); fwrite(gpath, 1, k + 1, o);
                                uint8_t z[1024] = {0}; fwrite(z, 1, 1000, o); fclose(o); printf("  wrote %s\n", nm); } }
                            free(gpath); fflush(stdout); }
                    }
                    if (ram[0x0e] == 4 || ram[0x0e] == 5) {
                        int five = ram[0x0e] == 5, y = ram[0xce], sk = 0;
                        if (diag && y >= 156) { static int nd; if (nd++ < 12)
                            printf("  low grab on core %ld: before x %.3f y %d.%03d yspd %d state %d -> y %d routine %d pad %02x\n", t,
                                   ((((long)r0[0x6d] << 8) | r0[0x86]) * 256 + r0[0x400]) / 256.0, r0[0xce], r0[0x416] * 1000 / 256, (int8_t)r0[0x9f], r0[0x1d], y, ram[0x0e], thispad); }
                        { long pxf = ((((long)r0[0x6d] << 8) | r0[0x86]) << 8) | r0[0x400];   /* x on the frame before the grab */
                          if (pxf < gminpx) gminpx = pxf; if (five && pxf < gminpx5) gminpx5 = pxf; }
                        if (five) g5++; else g4++;
                        gy[y]++;
                        if (five && first5 < 0) { first5 = t; printf("  first glitch grab (routine 5) on core %ld, y %d\n", t, y);
                            uint8_t *gpath = malloc(k + 2); long gi = n;
                            for (long q = k; q >= 1; q--) { gpath[q - 1] = meta[q][gi].pad; gi = meta[q][gi].parent; }
                            gpath[k] = thispad;
                            printf("  its last 12 pads:"); for (long q = k > 11 ? k - 11 : 0; q <= k; q++) printf(" %02x", gpath[q]); printf("\n");
                            if (outpath) { FILE *o = fopen(outpath, "wb"); if (o) { fwrite(in, 1, F0 + input_skip, o); fwrite(gpath, 1, k + 1, o);
                                uint8_t z[1024] = {0}; fwrite(z, 1, 1000, o); fclose(o); printf("  wrote %s (movie prefix + path + zeros)\n", outpath); } }
                            free(gpath); fflush(stdout); }
                        long jw = 0;
                        for (int j = 0; j < 6 && !sk; j++) { if (ram[0x746]) sk = 1; else { cur_pad = 0; retro_run(); RAMP(); steps++; jw++; } }
                        /* --walk N: for grabs up to core N, follow the automatic slide/wait/walk to the
                         * castle door and tally the entry frame (the level's framerule hangs on it) */
                        sk = sk || ram[0x746];          /* decided before the walk is followed */
                        if (!sk && t <= walkto) {
                            while (jw < 260 && !ram[0x746]) { cur_pad = 0; retro_run(); RAMP(); steps++; jw++; }
                            long cf = ram[0x746] ? t + jw : -1;
                            if (cf >= 0 && cf - F0 < 600) {
                                cas[cf - F0]++;
                                if (casbest < 0 || cf < casbest) {
                                    casbest = cf; free(caspath); caspath = malloc(k + 2); long idx = n; caslen = k + 1;
                                    for (long q = k; q >= 1; q--) { caspath[q - 1] = meta[q][idx].pad; idx = meta[q][idx].parent; }
                                    caspath[k] = thispad; casgrab = t; casy = y; casfive = five;
                                }
                            }
                        }
                        if (sk) {
                            nskip++;
                            if (nskip <= show) {
                                uint8_t *path = malloc(k + 2); long idx = n;
                                for (long q = k; q >= 1; q--) { path[q - 1] = meta[q][idx].pad; idx = meta[q][idx].parent; }
                                path[k] = thispad;
                                printf("SKIP: grab on core %ld at y %d, castle entered at once.  pads from core %ld:", t, y, F0);
                                for (long q = 0; q <= k; q++) printf(" %02x", path[q]);
                                printf("\n");
                                if (nskip == 1 && outpath) { FILE *o = fopen(outpath, "wb"); if (!o) { perror(outpath); return 1; }
                                    fwrite(in, 1, F0 + input_skip, o); fwrite(path, 1, k + 1, o);
                                    uint8_t z[1024] = {0}; fwrite(z, 1, 1000, o); fclose(o); printf("wrote %s\n", outpath); }
                                free(path);
                            }
                        }
                        continue;
                    }
                    if (diag && (int8_t)r0[0x9f] < 0 && r0[0xce] >= 164 && r0[0xce] <= 169 && ((((long)r0[0x6d] << 8) | r0[0x86]) >= 3409)) { static int nr; if (nr++ < 12)
                        printf("  rising near the pole, core %ld: x %.3f y %d yspd %d xspd %d -> x %.3f y %d yspd %d xspd %d state %d pad %02x\n", t,
                               ((((long)r0[0x6d] << 8) | r0[0x86]) * 256 + r0[0x400]) / 256.0, r0[0xce], (int8_t)r0[0x9f], (int8_t)r0[0x57], xf / 256.0, ram[0xce], (int8_t)ram[0x9f], (int8_t)ram[0x57], ram[0x1d], thispad); }
                    if (ram[0x1d] == 0 && ram[0xce] == 176) { if (xf > gmax) gmax = xf; if (ram[0x700] >= 25 && xf > gmax25) gmax25 = xf; }
                    if ((int8_t)ram[0x9f] < 0 && ram[0xce] >= 165 && ram[0xce] <= 167 && xf > hop) hop = xf;
                    if (!set_add(&seen, flag_key(ram))) continue;
                    if (!tmpl[k + 1]) { tmpl[k + 1] = malloc(ssz); retro_serialize(tmpl[k + 1], ssz); }
                    if (nn >= capx) { capx *= 2; nxt = realloc(nxt, (size_t)capx * RAMSZ); if (!nxt) { fprintf(stderr, "out of memory\n"); return 1; } }
                    memcpy(nxt + nn * RAMSZ, ram, RAMSZ);
                    meta[k + 1][nn].parent = (int32_t)n; meta[k + 1][nn].pad = thispad; nn++;
                }
            }
            printf("  core %ld: %ld nodes  grabs slide %ld glitch %ld  skips %ld  left-drops %ld  floor max x %.3f  with speed byte >= 25: %.3f  rising at y 165-167: %.3f  (%.0fs, %ld steps)\n",
                   t + 1, nn, g4, g5, nskip, ndrop, gmax / 256.0, gmax25 / 256.0, hop / 256.0, now() - t0, steps);
            if (pickf_t == t + 1) {      /* --pickfloor Y F: write the movie to the right-most node standing at y Y after core F-1 */
                long bi = -1, bx = -1;
                for (long q = 0; q < nn; q++) { const uint8_t *r = nxt + q * RAMSZ;
                    long qx = ((((long)r[0x6d] << 8) | r[0x86]) << 8) | r[0x400];
                    if (r[0x1d] == 0 && r[0xce] == pickf_y && qx > bx && (pickf_xmax < 0 || (qx >> 8) <= pickf_xmax)) { bx = qx; bi = q; } }
                if (bi < 0) { printf("pickfloor: no node standing at y %ld\n", pickf_y); return 1; }
                uint8_t *gpath = malloc(k + 2); long gi = bi;
                for (long q = k + 1; q >= 1; q--) { gpath[q - 1] = meta[q][gi].pad; gi = meta[q][gi].parent; }
                FILE *o = fopen(outpath, "wb"); if (!o) { perror(outpath); return 1; }
                fwrite(in, 1, F0 + input_skip, o); fwrite(gpath, 1, k + 1, o); uint8_t z[1024] = {0}; fwrite(z, 1, 1000, o); fclose(o);
                printf("pickfloor: node at x %.3f y %ld after core %ld; movie written to %s (search it from core %ld)\n", bx / 256.0, pickf_y, t, outpath, t + 1);
                return 0;
            }
            if (thr_x >= 0) printf("    embedded at speed >= 20 so far: %ld (best speed %d)   through so far: %ld\n", nemb, embbest, nthr);
            fflush(stdout);
            if (nn == 0) { printf("frontier died out at core %ld\n", t); break; }
            if (nn > maxnodes) { printf("frontier %ld > maxnodes at core %ld\n", nn, t); break; }
            if (seen.n * 2 > seen.cap) { fprintf(stderr, "hash set too full\n"); return 1; }
            meta[k + 1] = realloc(meta[k + 1], (size_t)(nn + 1) * sizeof(Meta));
            cur = realloc(cur, (size_t)nn * RAMSZ); memcpy(cur, nxt, (size_t)nn * RAMSZ); ncur = nn;
        }
        printf("smallest x on the frame before a grab: %.3f (glitch grabs: %.3f)\n", gminpx / 256.0, gminpx5 < (1L << 40) ? gminpx5 / 256.0 : -1.0);
        printf("grab heights (y: count):"); for (int y = 0; y < 256; y++) if (gy[y]) printf(" %d:%ld", y, gy[y]); printf("\n");
        if (walkto >= 0) {
            printf("castle-entry frame after the automatic walk (core: grabs):"); for (int q = 0; q < 600; q++) if (cas[q]) printf(" %ld:%ld", F0 + q, cas[q]); printf("\n");
            if (casbest >= 0) { printf("earliest castle entry core %ld: grab on core %ld, y %d, routine %d.  pads from core %ld:", casbest, casgrab, casy, casfive ? 5 : 4, F0);
                for (long q = 0; q < caslen; q++) printf(" %02x", caspath[q]); printf("\n");
                if (outpath) { FILE *o = fopen(outpath, "wb"); if (!o) { perror(outpath); return 1; }
                    fwrite(in, 1, F0 + input_skip, o); fwrite(caspath, 1, caslen, o);
                    uint8_t z[1024] = {0}; fwrite(z, 1, 1000, o); fclose(o); printf("wrote %s\n", outpath); } }
        }
        printf("done: %ld steps in %.0fs, skips found %ld\n", steps, now() - t0, nskip);
        return 0;
    }

    if (mode == 9) {
        /* N5: blind single-byte sweep of a fixed (input-independent) sequence.  After core frame T,
         * poke every RAM address in [LO, HI] with each of a fixed value list, run the movie on, and
         * list every poke that makes the event come EARLIER than in the unpoked run.  Event: first
         * frame with RAM[--ev ADDR]==VAL (or non-zero with --ev-nz ADDR), counted only after
         * RAM[--ev-seen ADDR]==VAL has been observed when that option is given.  Most hits are
         * bytes the game would never hold; the point is to see every byte the sequence reads. */
        long T = tA;
        for (long i = 0; i <= T; i++) { cur_pad = in[i + input_skip]; retro_run(); }
        RAMP();
        void *S = malloc(ssz); retro_serialize(S, ssz);
        uint8_t orig[RAMSZ]; memcpy(orig, ram, RAMSZ);
        static const int vals[] = { 0x00,0x01,0x02,0x03,0x04,0x08,0x0c,0x10,0x18,0x19,0x1c,0x20,0x28,0x40,0x80,0xc0,0xfe,0xff };
        int nv = (int)(sizeof vals / sizeof vals[0]);
        long base = -1, nearly = 0, nlate = 0, nnever = 0, ntr = 0, naddr = 0; double t0 = now();
        for (long a = sw_lo - 1; a <= sw_hi; a++) {          /* a == sw_lo-1 is the unpoked baseline */
            int printed = 0;
            for (int q = 0; q < (a < sw_lo ? 1 : nv); q++) {
                if (a >= sw_lo && vals[q] == orig[a]) continue;
                retro_unserialize(S, ssz); RAMP();
                if (a >= sw_lo) ram[a] = (uint8_t)vals[q];
                long ev = -1; int seen = ev_seen_addr < 0;
                for (long i = T + 1; i <= T + sw_limit; i++) {
                    cur_pad = (i < nf) ? in[i + input_skip] : 0; retro_run(); RAMP();
                    if (!seen && ram[ev_seen_addr] == ev_seen_val) seen = 1;
                    if (seen && (ev_nz ? ram[ev_addr] != 0 : ram[ev_addr] == ev_val)) { ev = i; break; }
                }
                if (a < sw_lo) { base = ev; printf("ramsweep after core %ld: baseline event on core %ld; addresses $%04lx-$%04lx, %d values each, limit %ld frames\n", T, base, sw_lo, sw_hi, nv, sw_limit);
                    if (base < 0) { printf("no baseline event inside the limit\n"); return 1; } continue; }
                ntr++;
                if (ev < 0) nnever++; else if (ev > base) nlate++; else if (ev < base) { nearly++;
                    if (!printed) { printf("  $%04lx (holds $%02x):", a, orig[a]); printed = 1; naddr++; }
                    printf(" %02x:%ld", vals[q], ev - base); }
            }
            if (printed) { printf("\n"); fflush(stdout); }
        }
        printf("done: %ld pokes in %.0fs; earlier %ld (in %ld addresses), later %ld, never %ld\n", ntr, now() - t0, nearly, naddr, nlate, nnever);
        return 0;
    }

    if (mode == 8) {
        /* N4: a turn-around-and-enter-a-pipe search without Left+Right (Maru's 8-4 room 3).
         * --turn F0 D: every no-L+R input from core F0; goal = vertical pipe entry
         * (GameEngineSubroutine 3) with ScreenLeft >= --slmin on a frame <= D, at x pixel <= --xgoal.
         * Pads: 12 on the floor, plus the 6 Down pads when standing high (y <= 96); A/L/R while
         * rising, L/R while falling.  Dedup per frame on the full gameplay key.  A node is dropped
         * when it cannot reach the pipe even with the best leftward acceleration on every remaining
         * frame (1.79 units per frame, cap 40), or cannot still finish the scroll and return. */
        if (F0 < 0 || F1 <= F0) { fprintf(stderr, "--turn F0 D required\n"); return 2; }
        for (long i = 0; i < F0; i++) { cur_pad = in[i + input_skip]; retro_run(); }
        RAMP();
        long D = F1, nfr = D - F0 + 1, ncur = 1, capx = 1 << 12, steps = 0, nbound = 0, ngoal = 0;
        void **tmpl = calloc(nfr + 2, sizeof(void *)); Meta **meta = calloc(nfr + 2, sizeof(Meta *));
        uint8_t *cur = malloc(RAMSZ), *nxt = malloc((size_t)capx * RAMSZ);
        double *score = malloc((size_t)capx * sizeof(double));
        tmpl[0] = malloc(ssz); if (!retro_serialize(tmpl[0], ssz)) return 1;
        memcpy(cur, ram, RAMSZ);
        meta[0] = malloc(sizeof(Meta)); meta[0][0].parent = -1; meta[0][0].pad = 0;
        Set seen; set_init(&seen, 1u << 24);
        /* pad table: the air pads first (none/L/R, then with A), then the other floor pads, then with
         * --lr the four Left+Right floor pads (in the air L+R acts as L or R alone), then the Down pads */
        uint8_t fp[24]; int nfl = 0, ndn = 0;
        { static const uint8_t base[12] = { 0x00,0x40,0x80,0x01,0x41,0x81,0x02,0x42,0x82,0x03,0x43,0x83 };
          static const uint8_t lrp[4] = { 0xc0,0xc1,0xc2,0xc3 }, dnp[6] = { 0x20,0x60,0xa0,0x22,0x62,0xa2 }, dlr[2] = { 0xe0,0xe2 };
          for (int q = 0; q < 12; q++) fp[nfl++] = base[q];
          if (allow_lr) for (int q = 0; q < 4; q++) fp[nfl++] = lrp[q];
          for (int q = 0; q < 6; q++) fp[nfl + ndn++] = dnp[q];
          if (allow_lr) for (int q = 0; q < 2; q++) fp[nfl + ndn++] = dlr[q]; }
        double t0 = now(), xg = xgoal + 255.0 / 256.0;
        printf("turn search %ld..%ld  slmin %ld  xgoal %ld  start x %d y %d xspd %d SL %d\n", F0, D, slmin, xgoal,
               (ram[0x6d] << 8) | ram[0x86], ram[0xce], (int8_t)ram[0x57], (ram[0x71a] << 8) | ram[0x71c]);
        for (long k = 0; k < nfr; k++) {
            long t = F0 + k, nn = 0, nok = 0; double minx = 1e9;
            meta[k + 1] = malloc(((size_t)ncur * 24 + 1) * sizeof(Meta)); set_clear(&seen);
            for (long n = 0; n < ncur; n++) {
                const uint8_t *r0 = cur + n * RAMSZ;
                int floor = r0[0x1d] == 0, np = floor ? (r0[0xce] <= 96 ? nfl + ndn : nfl) : ((int8_t)r0[0x9f] < 0 ? 6 : 3);
                for (int p = 0; p < np; p++) {
                    retro_unserialize(tmpl[k], ssz); RAMP(); memcpy(ram, r0, RAMSZ);
                    cur_pad = fp[p]; retro_run(); RAMP(); steps++;
                    if (DEAD(ram)) continue;
                    long sl = ((long)ram[0x71a] << 8) | ram[0x71c];
                    double x = (((long)ram[0x6d] << 8) | ram[0x86]) + ram[0x400] / 256.0, v = (int8_t)ram[0x57];
                    if (ram[0x0e] == 3) {
                        if (sl < slmin) continue;       /* the game decides the entry itself; only the scroll is required here */
                        ngoal++;
                        if (ngoal <= show) {
                            uint8_t *path = malloc(k + 2); long idx = n;
                            for (long q = k; q >= 1; q--) { path[q - 1] = meta[q][idx].pad; idx = meta[q][idx].parent; }
                            path[k] = fp[p];
                            printf("GOAL: pipe entered on core %ld at x %.3f (area pointer $%02x, entrance page %u).  pads from core %ld:", t, x, ram[0x750], ram[0x751], F0);
                            for (long q = 0; q <= k; q++) printf(" %02x", path[q]);
                            printf("\n");
                            if (ngoal == 1 && outpath) { FILE *o = fopen(outpath, "wb"); if (!o) { perror(outpath); return 1; }
                                fwrite(in, 1, F0 + input_skip, o); fwrite(path, 1, k + 1, o);
                                uint8_t z[1024] = {0}; fwrite(z, 1, 1000, o); fclose(o); printf("wrote %s\n", outpath); }
                            free(path);
                        }
                        continue;
                    }
                    if (p >= nfl) continue;                /* Down without a pipe entry duplicates the plain pad */
                    if (ram[0x0e] != 8) continue;
                    /* bound: frames left after this one */
                    long rem = D - t; int ok = 1; double bx = x, bv = v;
                    if (sl >= slmin) {
                        for (long q = 0; q < rem; q++) { bv -= 1.79; if (bv < -40) bv = -40; bx += bv / 16.0; }
                        if (bx > xg) ok = 0;
                    } else {
                        long m = (slmin - sl + 2) / 3; bv = 0;
                        for (long q = 0; q < rem - m; q++) { bv -= 1.79; if (bv < -40) bv = -40; bx += bv / 16.0; }
                        if (rem - m < 0 || bx > xg) ok = 0;
                    }
                    if (!ok) { nbound++; continue; }
                    if (!set_add(&seen, state_key(ram))) continue;
                    if (!tmpl[k + 1]) { tmpl[k + 1] = malloc(ssz); retro_serialize(tmpl[k + 1], ssz); }
                    if (nn >= capx) { capx *= 2; nxt = realloc(nxt, (size_t)capx * RAMSZ); score = realloc(score, (size_t)capx * sizeof(double));
                        if (!nxt || !score) { fprintf(stderr, "out of memory\n"); return 1; } }
                    score[nn] = bx;
                    memcpy(nxt + nn * RAMSZ, ram, RAMSZ);
                    meta[k + 1][nn].parent = (int32_t)n; meta[k + 1][nn].pad = fp[p]; nn++;
                    if (sl >= slmin) { nok++; if (x < minx) minx = x; }
                }
            }
            printf("  core %ld: %ld nodes (%ld with the scroll done, leftmost x %.3f)  goals %ld  bound-drops %ld  (%.0fs, %ld steps)\n",
                   t + 1, nn, nok, nok ? minx : 0.0, ngoal, nbound, now() - t0, steps);
            fflush(stdout);
            if (ngoal) { printf("goal layer reached on core %ld\n", t); break; }
            if (nn == 0) { printf("frontier died out at core %ld: no pipe entry by core %ld\n", t, D); break; }
            if (nn > maxnodes) { printf("frontier %ld > maxnodes at core %ld\n", nn, t); break; }
            if (seen.n * 2 > seen.cap) { fprintf(stderr, "hash set too full\n"); return 1; }
            if (beam > 0) {
                /* bucket = what decides the kind of motion available next; rank = projected x at the deadline */
                BeamEnt *e = malloc((size_t)nn * sizeof(BeamEnt));
                for (long q = 0; q < nn; q++) { const uint8_t *r = nxt + q * RAMSZ; long sl = ((long)r[0x71a] << 8) | r[0x71c];
                    /* before the scroll is done the projected x says nothing useful (it favours nodes that
                     * are behind), so those nodes are also bucketed by speed band and by how much scroll
                     * is left, and ranked by x (further right first) */
                    int nd = sl < slmin; long left = nd ? slmin - sl : 0; if (left > 31) left = 31;
                    /* after the scroll is done the bucket also holds the x pixel: ranking a whole height
                     * class by projected x keeps only the leftmost nodes, and those are the ones that
                     * run into the pipe's corner (the Maru control lost his own line that way) */
                    uint8_t bk[14] = { r[0x1d], r[0xce], r[0x9f], r[0x33], r[0x45], r[0x700] >= 25, sl >= slmin, r[0x709], r[0x0d] & 0x80, r[0x703] != 0,
                                       nd ? (uint8_t)(((int8_t)r[0x57] + 64) / 3) : 0, (uint8_t)(left / 2), nd ? 0 : r[0x86], nd ? 0 : r[0x6d] };
                    e[q].b = fnv_add(1469598103934665603ULL, bk, 14);
                    e[q].s = nd ? -((((long)r[0x6d] << 8) | r[0x86]) + r[0x400] / 256.0) : score[q]; e[q].i = q; }
                qsort(e, (size_t)nn, sizeof(BeamEnt), cmp_beam);
                Meta *m2 = malloc((size_t)(nn + 1) * sizeof(Meta)); cur = realloc(cur, (size_t)nn * RAMSZ); long j = 0, run = 0;
                for (long q = 0; q < nn; q++) { run = (q && e[q].b == e[q - 1].b) ? run + 1 : 0; if (run >= beam) continue;
                    memcpy(cur + j * RAMSZ, nxt + e[q].i * RAMSZ, RAMSZ); m2[j] = meta[k + 1][e[q].i]; j++; }
                free(meta[k + 1]); meta[k + 1] = m2; free(e);
                if (j < nn) printf("    beam: kept %ld of %ld\n", j, nn);
                ncur = j;
                continue;
            }
            meta[k + 1] = realloc(meta[k + 1], (size_t)(nn + 1) * sizeof(Meta));
            cur = realloc(cur, (size_t)nn * RAMSZ); memcpy(cur, nxt, (size_t)nn * RAMSZ); ncur = nn;
        }
        printf("done: %ld steps in %.0fs, goals %ld\n", steps, now() - t0, ngoal);
        return 0;
    }

    /* ---- BFS ---- */
    if (F0 < 0 || F1 <= F0) { fprintf(stderr, "--bfs F0 F1 required\n"); return 2; }
    for (long i = 0; i < F0; i++) { cur_pad = in[i + input_skip]; retro_run(); }
    RAMP();
    if (DEAD(ram)) { fprintf(stderr, "dead before F0\n"); return 1; }
    long nfr = F1 - F0 + 1;
    void **tmpl = calloc(nfr + 1, sizeof(void *));        /* full savestate at the START of frame F0+k */
    Meta **meta = calloc(nfr + 1, sizeof(Meta *)); long *cnt = calloc(nfr + 1, sizeof(long));
    uint8_t *cur = malloc(RAMSZ), *nxt = NULL; long ncur = 1, capn = 0;
    tmpl[0] = malloc(ssz); if (!retro_serialize(tmpl[0], ssz)) return 1;
    memcpy(cur, ram, RAMSZ);
    meta[0] = malloc(sizeof(Meta)); meta[0][0].parent = -1; meta[0][0].pad = 0; cnt[0] = 1;
    Set seen; set_init(&seen, 1u << 21);
    long best_t = -1; double t0 = now(); long steps = 0;
    long bsp = -1, bslot = -1, rng = -1, flm = -1, flmy = -1;
    printf("bfs %ld..%ld pads", F0, F1); for (int p = 0; p < npads; p++) printf(" %02x", pads[p]); printf("  savestate %zu bytes\n", ssz);
    for (long k = 0; k < nfr; k++) {
        long t = F0 + k;                                   /* frame about to be simulated */
        /* optional checkpoint: keep only the nodes standing on the ground at the start of frame t */
        for (int g = 0; g < ngnd; g++) if (gnd[g] == t) {
            long j = 0;
            for (long n = 0; n < ncur; n++) if (cur[n * RAMSZ + 0x1d] == 0) {
                if (j != n) { memmove(cur + j * RAMSZ, cur + n * RAMSZ, RAMSZ); meta[k][j] = meta[k][n]; }
                j++;
            }
            printf("checkpoint core %ld: kept %ld grounded nodes of %ld\n", t, j, ncur);
            ncur = j;
            if (!ncur) { printf("no grounded node at the checkpoint\n"); return 1; }
            if (pick >= 0) {   /* stage 1: write the movie that reaches grounded node `pick` and stop */
                long n = pick < ncur ? pick : ncur - 1, idx = n;
                uint8_t *path = malloc(k + 1);
                for (long q = k; q >= 1; q--) { path[q - 1] = meta[q][idx].pad; idx = meta[q][idx].parent; }
                printf("picked grounded node %ld; jumps:", n);
                for (long q = 0; q < k; q++) if ((path[q] & 1) && (q == 0 || !(path[q - 1] & 1))) {
                    long e = q; while (e < k && (path[e] & 1)) e++; printf(" [%ld hold %ld]", F0 + q, e - q); }
                printf("\n");
                if (outpath) { FILE *o = fopen(outpath, "wb"); if (!o) { perror(outpath); return 1; }
                    fwrite(in, 1, F0 + input_skip, o); fwrite(path, 1, k, o);
                    uint8_t z[512]; memset(z, 0x82, sizeof z); fwrite(z, 1, 300, o); fclose(o);
                    printf("wrote %s: prefix through core %ld, then B+R filler\n", outpath, t - 1); }
                return 0;
            }
        }
        /* scene info from node 0.  At k == 0 anything already loaded is reported as such, since
         * its spawn frame is not known from here. */
        if (k == 0) {
            for (int q = 0; q < 5; q++) if (cur[0x16 + q] == 0x2d && cur[0x0f + q] == 1) {
                bsp = 0; bslot = q; rng = cur[0x6dc] ? cur[0x6dc] : -1;
                printf("scene: bowser already loaded at F0 in slot %d, range $%02x\n", q, cur[0x6dc]); }
            for (int q = 0; q < 5; q++) if (flm < 0 && cur[0x16 + q] == 0x15 && cur[0x0f + q] == 1) {
                flm = 0; flmy = cur[0xcf + q]; printf("scene: a flame already loaded at F0 in slot %d, y %ld\n", q, flmy); }
        }
        if (bsp < 0) for (int q = 0; q < 5; q++) if (cur[0x16 + q] == 0x2d && cur[0x0f + q] == 1) { bsp = t - 1; bslot = q; }
        if (bsp >= 0 && rng < 0 && cur[0x6dc]) { rng = cur[0x6dc]; printf("scene: bowser spawn core %ld slot %ld, range $%02lx set by core %ld (FC %u)\n", bsp, bslot, rng, t - 1, cur[0x09]); }
        if (flm < 0) for (int q = 0; q < 5; q++) if (cur[0x16 + q] == 0x15 && cur[0x0f + q] == 1) { flm = t - 1; flmy = cur[0xcf + q]; printf("scene: first flame core %ld slot %d y %ld\n", flm, q, flmy); }
        /* coast tests on the frontier of frame t: no input from t on */
        if (cA >= 0 && t >= cA && t <= cB && best_t < 0) {
            long nsucc = 0, nair = 0;
            for (long n = 0; n < ncur; n++) {
                const uint8_t *r = cur + n * RAMSZ;
                if (r[0x1d] == 0) continue;
                nair++;
                retro_unserialize(tmpl[k], ssz); RAMP(); memcpy(ram, r, RAMSZ);
                int won = 0; long vf = -1;
                for (long j = 0; j < 90; j++) { cur_pad = 0; retro_run(); RAMP(); steps++;
                    if (WON(ram)) { won = 1; vf = t + j; break; } if (DEAD(ram)) break; }
                if (!won) continue;
                nsucc++;
                if (nsucc <= show) {
                    /* reconstruct the pad path F0..t-1 */
                    uint8_t *path = malloc(k + 1); long idx = n;
                    for (long q = k; q >= 1; q--) { path[q - 1] = meta[q][idx].pad; idx = meta[q][idx].parent; }
                    printf("SUCCESS last_input=%ld victory=%ld  jumps:", t - 1, vf);
                    for (long q = 0; q < k; q++) if ((path[q] & 1) && (q == 0 || !(path[q - 1] & 1))) {
                        long e = q; while (e < k && (path[e] & 1)) e++; printf(" [%ld hold %ld]", F0 + q, e - q); }
                    printf("\n");
                    if (nsucc == 1 && outpath) {
                        FILE *o = fopen(outpath, "wb"); if (!o) { perror(outpath); return 1; }
                        fwrite(in, 1, F0 + input_skip, o); fwrite(path, 1, k, o);
                        uint8_t z[256] = {0}; fwrite(z, 1, 200, o); fclose(o);
                        printf("wrote %s (%ld frames)\n", outpath, F0 + input_skip + k + 200);
                    }
                    free(path);
                }
            }
            printf("coast t=%ld: %ld airborne of %ld nodes tested, successes %ld\n", t, nair, ncur, nsucc);
            if (nsucc) { best_t = t; printf("BEST last input = core %ld   (WR 17846)\n", t - 1); break; }
        }
        if (k == nfr - 1) break;
        /* expand */
        if ((ncur * npads) > capn) { capn = ncur * npads + 1024; nxt = realloc(nxt, (size_t)capn * RAMSZ); }
        meta[k + 1] = malloc((size_t)(ncur * npads + 1) * sizeof(Meta));
        long nn = 0; set_clear(&seen);
        for (long n = 0; n < ncur; n++) for (int p = 0; p < npads; p++) {
            retro_unserialize(tmpl[k], ssz); RAMP(); memcpy(ram, cur + n * RAMSZ, RAMSZ);
            cur_pad = pads[p]; retro_run(); RAMP(); steps++;
            if (DEAD(ram)) continue;
            if (WON(ram)) { printf("note: victory during expansion at core %ld (last input <= %ld)\n", t, t); continue; }
            /* a stomped Hammer Bro forks the world once per stomp frame and multiplies the frontier;
             * the bounce buys nothing here, so stomp branches are dropped unless --allow-stomp */
            if (!allow_stomp) { int st = 0; for (int q = 0; q < 5; q++) if (ram[0x16 + q] == 0x05 && (ram[0x1e + q] & 0x20)) st = 1; if (st) { nstomp++; continue; } }
            if (!set_add(&seen, state_key(ram))) continue;
            if (!tmpl[k + 1]) { tmpl[k + 1] = malloc(ssz); retro_serialize(tmpl[k + 1], ssz); }
            memcpy(nxt + nn * RAMSZ, ram, RAMSZ);
            meta[k + 1][nn].parent = (int32_t)n; meta[k + 1][nn].pad = pads[p]; nn++;
        }
        /* position prune: a node that bumped terrain and fell behind the best x can never catch up
         * (cap speed is the maximum), so only the furthest-forward nodes are kept */
        if (xprune && nn > 0) {
            long xmax = -1, j = 0;
            for (long n = 0; n < nn; n++) { const uint8_t *r = nxt + n * RAMSZ; long x = ((long)r[0x6d] << 16) | ((long)r[0x86] << 8) | r[0x400]; if (x > xmax) xmax = x; }
            for (long n = 0; n < nn; n++) { const uint8_t *r = nxt + n * RAMSZ; long x = ((long)r[0x6d] << 16) | ((long)r[0x86] << 8) | r[0x400];
                if (x != xmax) continue;
                if (j != n) { memmove(nxt + j * RAMSZ, nxt + n * RAMSZ, RAMSZ); meta[k + 1][j] = meta[k + 1][n]; }
                j++; }
            nxdrop += nn - j; nn = j;
        }
        cnt[k + 1] = nn;
        if (nn == 0) { printf("frontier died out at core %ld\n", t); break; }
        if (nn > maxnodes) { printf("frontier %ld > maxnodes at core %ld\n", nn, t); break; }
        if (seen.n * 2 > seen.cap) { fprintf(stderr, "hash set too full\n"); return 1; }
        { uint8_t *sw = cur; cur = nxt; nxt = sw; }
        ncur = nn;
        /* the old frontier buffer becomes the next write target: size it for every child */
        nxt = realloc(nxt, (size_t)(ncur * npads + 1024) * RAMSZ); capn = ncur * npads + 1024;
        if ((k % 10) == 9 || k < 3) {
            printf("  core %ld: %ld nodes  (%.0fs, %ld steps, %ld stomp-drops, %ld x-drops)\n", t + 1, ncur, now() - t0, steps, nstomp, nxdrop); fflush(stdout);
            if (diag) {   /* how many nodes stand, and how many distinct worlds (enemy + misc object state) */
                long ng = 0; Set w; set_init(&w, 1u << 16);
                for (long n = 0; n < ncur; n++) { const uint8_t *r = cur + n * RAMSZ; if (r[0x1d] == 0) ng++;
                    uint64_t hh = 1469598103934665603ULL; hh = fnv_add(hh, r + 0x0f, 0x0e); hh = fnv_add(hh, r + 0x1e, 0x15);
                    hh = fnv_add(hh, r + 0x6e, 0x05); hh = fnv_add(hh, r + 0x87, 0x05); hh = fnv_add(hh, r + 0xcf, 0x05); set_add(&w, hh); }
                printf("    diag: grounded %ld, distinct enemy-worlds %u\n", ng, w.n); free(w.keys);
            }
        }
    }
    if (best_t < 0) printf("no success in the coast window\n");
    printf("done: %ld steps in %.0fs\n", steps, now() - t0);
    (void)cnt;
    return 0;
}
