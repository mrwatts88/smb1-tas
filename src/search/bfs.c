/* Frame-layered BFS over SMB1 states with a libretro core (P2.1 v1, single-threaded).
 *
 *   bfs CORE.so ROM.nes INPUTS.bin --root F [--input-skip 2] [--layers N] [--mem-mb M]
 *       [--out DIR] [--replay-check] [--quiet-terminals]
 *       [--deadline G --target-x PX [--max-speed 40] [--accel 2] [--bound accel|greedy] [--margin U]]
 *   --bound accel  (default, sound): speed may grow by ACCEL per frame up to MAX_SPEED.
 *   --bound greedy (aggressive, NOT proven sound): exact simulation of the ground-running dynamics
 *                  (subpixel $0705 += $E4 with carry into speed, cap, then x += 16*speed) — ignores
 *                  the doubled adder while facing != moving direction. A solution found under it is still
 *                  a real solution (the core verifies); only a 'no solution' needs the sound bound.
 *   --margin U     units (1/256 px) added to the bound.
 *   Deadline pruning (exact given the bounds): a state after frame f is dropped when even accelerating by
 *   ACCEL speed units per frame up to MAX_SPEED (1/16 px per frame) it cannot reach x >= PX pixels by
 *   frame G (the latest frame at which a flagpole grab can still beat the target; see the experiment file).
 *
 * Root = state after running frames 0..F with the movie inputs (QuickNES frame numbering; with
 * --input-skip 2 QuickNES frame j uses fm2 record j+2, and QuickNES row j+1 = FCEUX row j+4).
 * From the root, every layer expands each distinct state with the 16 combinations of A/B/Left/Right
 * (Up/Down/Start/Select never pressed). Distinct = FNV-1a 64 hash of RAM $0000-$00FF and
 * $0300-$07FF (stack and OAM buffer excluded). Terminal = GameEngineSubroutine ($0E) becomes 4 or 5
 * (flagpole touched): the state is run input-free until StarFlagTaskControl ($0746) = 4 to get
 * T_set (the framerule-relevant frame, F27/F32); dead = GES 6/11 or Player_Y_HighPos > 1.
 * Prints one line per layer; at the end writes DIR/best_inputs.bin (frames 0..T_set, movie inputs
 * up to the root then the found path) and DIR/terminals.txt.
 * --replay-check: instead of searching, replay the movie's own inputs from the root and report the
 * grab frame and T_set (evaluator sanity check).
 */
#include <dlfcn.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <libretro.h>

static uint8_t cur_pad;
static void log_cb(enum retro_log_level l, const char *f, ...) { (void)l; (void)f; }
static struct retro_log_callback logcb = { log_cb };
static bool env_cb(unsigned cmd, void *data) {
    switch (cmd) {
    case RETRO_ENVIRONMENT_SET_PIXEL_FORMAT: return true;
    case RETRO_ENVIRONMENT_GET_CAN_DUPE: *(bool *)data = true; return true;
    case RETRO_ENVIRONMENT_GET_LOG_INTERFACE: *(struct retro_log_callback *)data = logcb; return true;
    case RETRO_ENVIRONMENT_GET_SYSTEM_DIRECTORY: case RETRO_ENVIRONMENT_GET_SAVE_DIRECTORY: *(const char **)data = "."; return true;
    case RETRO_ENVIRONMENT_SET_MEMORY_MAPS: case RETRO_ENVIRONMENT_SET_INPUT_DESCRIPTORS:
    case RETRO_ENVIRONMENT_SET_CONTROLLER_INFO: case RETRO_ENVIRONMENT_SET_GEOMETRY: case RETRO_ENVIRONMENT_SET_SUPPORT_NO_GAME: return true;
    case RETRO_ENVIRONMENT_GET_VARIABLE: {
        struct retro_variable *v = (struct retro_variable *)data;
        if (!strcmp(v->key, "quicknes_up_down_allowed")) { v->value = "enabled"; return true; }
        if (!strcmp(v->key, "quicknes_no_sprite_limit")) { v->value = "disabled"; return true; }
        return false; }
    case RETRO_ENVIRONMENT_GET_VARIABLE_UPDATE: *(bool *)data = false; return true;
    default: return false;
    }
}
static void video_cb(const void *d, unsigned w, unsigned h, size_t p) { (void)d; (void)w; (void)h; (void)p; }
static void audio_cb(int16_t l, int16_t r) { (void)l; (void)r; }
static size_t audio_batch_cb(const int16_t *d, size_t n) { (void)d; return n; }
static void input_poll_cb(void) {}
static int16_t input_state_cb(unsigned port, unsigned dev, unsigned idx, unsigned id) {
    (void)idx; if (port != 0 || (dev & 0xff) != RETRO_DEVICE_JOYPAD) return 0;
    uint8_t p = cur_pad;
    if (id == RETRO_DEVICE_ID_JOYPAD_MASK) {
        int16_t m = 0;
        if (p & 0x01) m |= 1 << RETRO_DEVICE_ID_JOYPAD_A; if (p & 0x02) m |= 1 << RETRO_DEVICE_ID_JOYPAD_B;
        if (p & 0x04) m |= 1 << RETRO_DEVICE_ID_JOYPAD_SELECT; if (p & 0x08) m |= 1 << RETRO_DEVICE_ID_JOYPAD_START;
        if (p & 0x10) m |= 1 << RETRO_DEVICE_ID_JOYPAD_UP; if (p & 0x20) m |= 1 << RETRO_DEVICE_ID_JOYPAD_DOWN;
        if (p & 0x40) m |= 1 << RETRO_DEVICE_ID_JOYPAD_LEFT; if (p & 0x80) m |= 1 << RETRO_DEVICE_ID_JOYPAD_RIGHT;
        return m; }
    switch (id) {
    case RETRO_DEVICE_ID_JOYPAD_A: return (p & 0x01) != 0; case RETRO_DEVICE_ID_JOYPAD_B: return (p & 0x02) != 0;
    case RETRO_DEVICE_ID_JOYPAD_SELECT: return (p & 0x04) != 0; case RETRO_DEVICE_ID_JOYPAD_START: return (p & 0x08) != 0;
    case RETRO_DEVICE_ID_JOYPAD_UP: return (p & 0x10) != 0; case RETRO_DEVICE_ID_JOYPAD_DOWN: return (p & 0x20) != 0;
    case RETRO_DEVICE_ID_JOYPAD_LEFT: return (p & 0x40) != 0; case RETRO_DEVICE_ID_JOYPAD_RIGHT: return (p & 0x80) != 0;
    default: return 0; }
}
#define SYM(name) static name##_t name; name = (name##_t)dlsym(h, #name); if (!name) { fprintf(stderr, "missing %s\n", #name); exit(1); }
typedef void (*retro_set_environment_t)(retro_environment_t); typedef void (*retro_set_video_refresh_t)(retro_video_refresh_t);
typedef void (*retro_set_audio_sample_t)(retro_audio_sample_t); typedef void (*retro_set_audio_sample_batch_t)(retro_audio_sample_batch_t);
typedef void (*retro_set_input_poll_t)(retro_input_poll_t); typedef void (*retro_set_input_state_t)(retro_input_state_t);
typedef void (*retro_init_t)(void); typedef bool (*retro_load_game_t)(const struct retro_game_info *);
typedef void (*retro_run_t)(void); typedef size_t (*retro_serialize_size_t)(void);
typedef bool (*retro_serialize_t)(void *, size_t); typedef bool (*retro_unserialize_t)(const void *, size_t);
typedef void *(*retro_get_memory_data_t)(unsigned);

static double now(void) { struct timespec t; clock_gettime(CLOCK_MONOTONIC, &t); return t.tv_sec + t.tv_nsec * 1e-9; }
static uint64_t hash_ram(const uint8_t *ram) {
    uint64_t h = 1469598103934665603ULL;
    for (int i = 0; i < 0x100; i++) { h ^= ram[i]; h *= 1099511628211ULL; }
    for (int i = 0x300; i < 0x800; i++) { h ^= ram[i]; h *= 1099511628211ULL; }
    return h;
}

/* ---- per-layer storage ---- */
typedef struct { uint32_t parent; uint8_t input; } link_t;
typedef struct {
    uint32_t n, cap; size_t ssz;
    uint8_t *blobs;         /* cap * ssz */
    uint64_t *hashes;       /* cap */
    uint32_t *table; uint32_t tcap; /* open addressing: index+1, 0 = empty */
    link_t *links;          /* cap */
} layer_t;
static void layer_init(layer_t *L, uint32_t cap, size_t ssz) {
    L->n = 0; L->cap = cap; L->ssz = ssz;
    L->blobs = malloc((size_t)cap * ssz); L->hashes = malloc(cap * sizeof(uint64_t));
    L->tcap = 1; while (L->tcap < cap * 2) L->tcap <<= 1;
    L->table = calloc(L->tcap, sizeof(uint32_t)); L->links = malloc(cap * sizeof(link_t));
    if (!L->blobs || !L->hashes || !L->table || !L->links) { fprintf(stderr, "out of memory\n"); exit(1); }
}
static void layer_clear(layer_t *L) { L->n = 0; memset(L->table, 0, L->tcap * sizeof(uint32_t)); }
/* returns index if inserted, -1 if duplicate, -2 if full */
static long layer_insert(layer_t *L, uint64_t hsh, const uint8_t *blob, uint32_t parent, uint8_t input) {
    uint32_t mask = L->tcap - 1, i = (uint32_t)(hsh ^ (hsh >> 32)) & mask;
    while (L->table[i]) { uint32_t j = L->table[i] - 1; if (L->hashes[j] == hsh) return -1; i = (i + 1) & mask; }
    if (L->n >= L->cap) return -2;
    uint32_t j = L->n++; L->table[i] = j + 1; L->hashes[j] = hsh;
    memcpy(L->blobs + (size_t)j * L->ssz, blob, L->ssz); L->links[j].parent = parent; L->links[j].input = input;
    return j;
}

int main(int argc, char **argv) {
    if (argc < 4) { fprintf(stderr, "usage: see header\n"); return 2; }
    const char *core = argv[1], *rom = argv[2], *inputs = argv[3], *outdir = "runs/bfs";
    long root = -1, layers = 400, mem_mb = 4000, input_skip = 0; int replay_check = 0, quiet_t = 0;
    long deadline = -1, target_x = -1, max_speed = 40, accel = 2, margin = 0; int greedy = 0;
    for (int i = 4; i < argc; i++) {
        if (!strcmp(argv[i], "--root")) root = atol(argv[++i]);
        else if (!strcmp(argv[i], "--layers")) layers = atol(argv[++i]);
        else if (!strcmp(argv[i], "--mem-mb")) mem_mb = atol(argv[++i]);
        else if (!strcmp(argv[i], "--input-skip")) input_skip = atol(argv[++i]);
        else if (!strcmp(argv[i], "--out")) outdir = argv[++i];
        else if (!strcmp(argv[i], "--replay-check")) replay_check = 1;
        else if (!strcmp(argv[i], "--quiet-terminals")) quiet_t = 1;
        else if (!strcmp(argv[i], "--deadline")) deadline = atol(argv[++i]);
        else if (!strcmp(argv[i], "--target-x")) target_x = atol(argv[++i]);
        else if (!strcmp(argv[i], "--max-speed")) max_speed = atol(argv[++i]);
        else if (!strcmp(argv[i], "--accel")) accel = atol(argv[++i]);
        else if (!strcmp(argv[i], "--margin")) margin = atol(argv[++i]);
        else if (!strcmp(argv[i], "--bound")) greedy = !strcmp(argv[++i], "greedy");
        else { fprintf(stderr, "unknown option %s\n", argv[i]); return 2; }
    }
    if (root < 0) { fprintf(stderr, "--root required\n"); return 2; }
    void *h = dlopen(core, RTLD_NOW | RTLD_LOCAL); if (!h) { fprintf(stderr, "dlopen: %s\n", dlerror()); return 1; }
    SYM(retro_set_environment) SYM(retro_set_video_refresh) SYM(retro_set_audio_sample) SYM(retro_set_audio_sample_batch)
    SYM(retro_set_input_poll) SYM(retro_set_input_state) SYM(retro_init) SYM(retro_load_game) SYM(retro_run)
    SYM(retro_serialize_size) SYM(retro_serialize) SYM(retro_unserialize) SYM(retro_get_memory_data)
    FILE *f = fopen(inputs, "rb"); if (!f) { perror(inputs); return 1; }
    fseek(f, 0, SEEK_END); long nin = ftell(f); fseek(f, 0, SEEK_SET); uint8_t *in = malloc(nin);
    if (fread(in, 1, nin, f) != (size_t)nin) return 1; fclose(f);
    FILE *rf = fopen(rom, "rb"); if (!rf) { perror(rom); return 1; }
    fseek(rf, 0, SEEK_END); long rsz = ftell(rf); fseek(rf, 0, SEEK_SET); void *rdata = malloc(rsz);
    if (fread(rdata, 1, rsz, rf) != (size_t)rsz) return 1; fclose(rf);
    retro_set_environment(env_cb); retro_set_video_refresh(video_cb); retro_set_audio_sample(audio_cb);
    retro_set_audio_sample_batch(audio_batch_cb); retro_set_input_poll(input_poll_cb); retro_set_input_state(input_state_cb);
    retro_init();
    struct retro_game_info gi = { rom, rdata, (size_t)rsz, NULL };
    if (!retro_load_game(&gi)) { fprintf(stderr, "load failed\n"); return 1; }
    uint8_t *ram = retro_get_memory_data(RETRO_MEMORY_SYSTEM_RAM);
    size_t ssz = retro_serialize_size();
    #define PAD(j) ((j) + input_skip < nin ? in[(j) + input_skip] : 0)
    for (long j = 0; j <= root; j++) { cur_pad = PAD(j); retro_run(); }
    uint8_t *rootblob = malloc(ssz); retro_serialize(rootblob, ssz);
    printf("root after frame %ld: GES=%u OperMode_Task=%u X=%u page=%u Y=%u timer=%u%u%u state=%zu bytes\n",
           root, ram[0x0e], ram[0x772], ram[0x86], ram[0x6d], ram[0xce], ram[0x7f8], ram[0x7f9], ram[0x7fa], ssz);

    if (replay_check) {
        long fr = root; int grab = -1;
        while (fr < root + 2000) { fr++; cur_pad = PAD(fr); retro_run();
            if (grab < 0 && (ram[0x0e] == 4 || ram[0x0e] == 5)) { grab = (int)fr; printf("grab after frame %ld: GES=%u Y=%u X=%u timer=%u%u%u\n", fr, ram[0x0e], ram[0xce], ram[0x86], ram[0x7f8], ram[0x7f9], ram[0x7fa]); }
            if (ram[0x746] == 4) { printf("T_set after frame %ld (ITC=%u)\n", fr, ram[0x77f]); break; } }
        return 0;
    }

    if (deadline >= 0 && layers > deadline - root) layers = deadline - root;
    uint32_t cap = (uint32_t)(((size_t)mem_mb << 20) / 2 / (ssz + 32));
    layer_t A, B; layer_init(&A, cap, ssz); layer_init(&B, cap, ssz);
    layer_t *cur = &A, *nxt = &B;
    layer_insert(cur, hash_ram(ram), rootblob, 0, 0);
    link_t **links = malloc((layers + 1) * sizeof(link_t *)); uint32_t *counts = malloc((layers + 1) * sizeof(uint32_t));
    static const uint8_t INPUTS[16] = { 0x00, 0x01, 0x02, 0x03, 0x40, 0x41, 0x42, 0x43, 0x80, 0x81, 0x82, 0x83, 0xc0, 0xc1, 0xc2, 0xc3 };
    uint8_t *tmp = malloc(ssz), *child = malloc(ssz);
    char path[1024]; snprintf(path, sizeof path, "%s/terminals.txt", outdir); FILE *tf = fopen(path, "w");
    if (!tf) { perror(path); return 1; }
    long best_tset = -1, best_layer = -1; uint32_t best_idx = 0; uint8_t best_input = 0; long nterm = 0;
    double t0 = now();
    for (long L = 0; L < layers; L++) {
        layer_clear(nxt); long dup = 0, dead = 0, term = 0, full = 0, pruned = 0; double tl = now();
        long frames_left = deadline >= 0 ? deadline - (root + L + 1) : -1;
        for (uint32_t p = 0; p < cur->n; p++) {
            const uint8_t *pb = cur->blobs + (size_t)p * ssz;
            for (int k = 0; k < 16; k++) {
                retro_unserialize(pb, ssz); cur_pad = INPUTS[k]; retro_run();
                uint8_t ges = ram[0x0e];
                if (ges == 4 || ges == 5) {
                    long fr = root + L + 1; int grab = (int)fr; uint8_t gy = ram[0xce], gx = ram[0x86];
                    int T = ram[0x7f8] * 100 + ram[0x7f9] * 10 + ram[0x7fa];
                    while (fr < grab + 1200 && ram[0x746] != 4) { fr++; cur_pad = 0; retro_run(); }
                    long tset = ram[0x746] == 4 ? fr : -1; term++; nterm++;
                    if (!quiet_t || (best_tset < 0 || tset < best_tset))
                        fprintf(tf, "layer %ld grab_after_frame %d GES %u Y %u X %u T %d T_set %ld parent %u input %02x\n", L, grab, ges, gy, gx, T, tset, p, INPUTS[k]);
                    if (tset >= 0 && (best_tset < 0 || tset < best_tset)) { best_tset = tset; best_layer = L; best_idx = p; best_input = INPUTS[k]; }
                    continue;
                }
                if (ges == 6 || ges == 11 || ram[0xb5] > 1) { dead++; continue; }
                if (deadline >= 0 && ges == 8) {   /* only once the player is under control (position valid) */
                    long xt = ((long)(ram[0x6d] << 8 | ram[0x86]) << 8) | ram[0x705];
                    long sp = (int8_t)ram[0x57], gain = 0;
                    if (greedy) {
                        long mf = ram[0x705], x = (ram[0x6d] << 8 | ram[0x86]);
                        for (long k = 1; k <= frames_left; k++) {
                            mf += 0xe4; if (mf > 0xff) { mf -= 0x100; sp++; } if (sp > max_speed) sp = max_speed;
                            mf += (sp << 4) & 0xff; x += (sp >> 4) + (mf >> 8); mf &= 0xff;
                        }
                        gain = (x << 8 | mf) - xt;
                    } else
                        for (long k = 1; k <= frames_left; k++) { sp += accel; if (sp > max_speed) sp = max_speed; gain += 16 * sp; }
                    if (xt + gain + margin < target_x * 256) { pruned++; continue; }
                }
                retro_serialize(child, ssz);
                long r = layer_insert(nxt, hash_ram(ram), child, p, INPUTS[k]);
                if (r == -1) dup++; else if (r == -2) full++;
            }
        }
        links[L] = malloc((size_t)nxt->n * sizeof(link_t)); memcpy(links[L], nxt->links, (size_t)nxt->n * sizeof(link_t)); counts[L] = nxt->n;
        printf("layer %ld (after frame %ld): parents %u -> unique %u, dup %ld, dead %ld, pruned %ld, terminal %ld, full %ld; best T_set %ld; %.1fs (total %.0fs)\n",
               L + 1, root + L + 1, cur->n, nxt->n, dup, dead, pruned, term, full, best_tset, now() - tl, now() - t0);
        fflush(stdout); fflush(tf);
        if (full) { printf("LAYER FULL (cap %u states) — stop; raise --mem-mb or prune\n", cap); break; }
        if (nxt->n == 0) { printf("no live states left\n"); break; }
        layer_t *t = cur; cur = nxt; nxt = t;
        if (best_tset >= 0 && L + 1 >= best_layer + 60) { printf("terminal found; stopping 60 layers after the best\n"); break; }
    }
    fclose(tf);
    printf("terminals: %ld; best T_set after frame %ld (layer %ld)\n", nterm, best_tset, best_layer);
    if (best_tset >= 0) {
        /* reconstruct: best terminal = child of state best_idx in layer best_layer (links[best_layer-1] describe that layer's states) */
        long npath = best_layer + 1; uint8_t *seq = malloc(npath); seq[best_layer] = best_input; uint32_t idx = best_idx;
        for (long L = best_layer - 1; L >= 0; L--) { seq[L] = links[L][idx].input; idx = links[L][idx].parent; }
        snprintf(path, sizeof path, "%s/best_inputs.bin", outdir); FILE *bf = fopen(path, "wb");
        for (long j = 0; j <= root; j++) fputc(PAD(j), bf);
        fwrite(seq, 1, npath, bf); fclose(bf);
        printf("wrote %s (%ld frames: movie to root, then %ld searched inputs)\n", path, root + 1 + npath, npath);
    }
    return 0;
}
