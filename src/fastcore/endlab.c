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
