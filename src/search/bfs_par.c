/* Frame-layered BFS v2 (P2.1b): compact 2 KiB RAM states + template savestate, forked workers.
 *
 *   bfs_par CORE.so ROM.nes INPUTS.bin --root F [--input-skip 2] [--layers N] [--mem-mb M] [--workers K]
 *           [--out DIR] [--deadline G --target-x PX [--max-speed 40] [--accel 2] [--margin U]] [--quiet-terminals]
 *
 * Same semantics as bfs.c (see there) except: a state is the 2 KiB system RAM; to expand it the RAM is
 * patched into a template savestate taken at the root (RAM offset found by probing, F50) and
 * unserialized. Each layer: parents are split into chunks; K forked workers (each with its own copy of
 * the core) expand 1/K of a chunk into a shared-memory arena (hash, parent, input, ram); the parent
 * process merges the arenas into the next layer with an open-addressing hash table. Terminals (GES 4/5)
 * are evaluated in the worker (run input-free to StarFlagTaskControl = 4) and reported.
 * Output: DIR/terminals.txt, DIR/best_inputs.bin, per-layer lines on stdout.
 */
#include <dlfcn.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>
#include <sys/mman.h>
#include <sys/wait.h>
#include <libretro.h>

#define RAMSZ 0x800
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
    case RETRO_ENVIRONMENT_GET_VARIABLE: { struct retro_variable *v = data;
        if (!strcmp(v->key, "quicknes_up_down_allowed")) { v->value = "enabled"; return true; }
        if (!strcmp(v->key, "quicknes_no_sprite_limit")) { v->value = "disabled"; return true; } return false; }
    case RETRO_ENVIRONMENT_GET_VARIABLE_UPDATE: *(bool *)data = false; return true;
    default: return false; }
}
static void video_cb(const void *d, unsigned w, unsigned h, size_t p) { (void)d; (void)w; (void)h; (void)p; }
static void audio_cb(int16_t l, int16_t r) { (void)l; (void)r; }
static size_t audio_batch_cb(const int16_t *d, size_t n) { (void)d; return n; }
static void input_poll_cb(void) {}
static int16_t input_state_cb(unsigned port, unsigned dev, unsigned idx, unsigned id) {
    (void)idx; if (port || (dev & 0xff) != RETRO_DEVICE_JOYPAD) return 0; uint8_t p = cur_pad;
    static const int map[9] = { 0x02, 0, 0x04, 0x08, 0x10, 0x20, 0x40, 0x80, 0x01 }; /* B Y SEL START U D L R A */
    if (id == RETRO_DEVICE_ID_JOYPAD_MASK) { int16_t m = 0; for (int i = 0; i < 9; i++) if (p & map[i]) m |= 1 << i; return m; }
    return id < 9 && (p & map[id]) ? 1 : 0;
}
typedef void (*retro_run_t)(void); typedef size_t (*retro_serialize_size_t)(void);
typedef bool (*retro_serialize_t)(void *, size_t); typedef bool (*retro_unserialize_t)(const void *, size_t);
static retro_run_t c_run; static retro_serialize_t c_ser; static retro_unserialize_t c_unser;
static uint8_t *ram; static size_t ssz; static long ram_off = -1;

static double now(void) { struct timespec t; clock_gettime(CLOCK_MONOTONIC, &t); return t.tv_sec + t.tv_nsec * 1e-9; }
static uint64_t hash_ram(const uint8_t *r) {
    uint64_t h = 1469598103934665603ULL;
    for (int i = 0; i < 0x100; i++) { h ^= r[i]; h *= 1099511628211ULL; }
    for (int i = 0x300; i < 0x800; i++) { h ^= r[i]; h *= 1099511628211ULL; }
    return h;
}
typedef struct { uint32_t parent; uint8_t input; } link_t;
typedef struct { uint64_t hash; uint32_t parent; uint8_t input; uint8_t pad[3]; uint8_t ram[RAMSZ]; } rec_t;
typedef struct { long layer, grab, tset; int T; uint8_t ges, y, x, input; uint32_t parent; } term_t;
typedef struct { uint32_t n, cap; uint8_t *blobs; uint64_t *hashes; uint32_t *table; uint32_t tcap; link_t *links; } layer_t;
static void layer_init(layer_t *L, uint32_t cap) {
    L->n = 0; L->cap = cap; L->blobs = malloc((size_t)cap * RAMSZ); L->hashes = malloc(cap * sizeof(uint64_t));
    L->tcap = 1; while (L->tcap < cap * 2) L->tcap <<= 1; L->table = calloc(L->tcap, sizeof(uint32_t)); L->links = malloc(cap * sizeof(link_t));
    if (!L->blobs || !L->hashes || !L->table || !L->links) { fprintf(stderr, "out of memory\n"); exit(1); }
}
static void layer_clear(layer_t *L) { L->n = 0; memset(L->table, 0, L->tcap * sizeof(uint32_t)); }
static long layer_insert(layer_t *L, uint64_t hsh, const uint8_t *blob, uint32_t parent, uint8_t input) {
    uint32_t mask = L->tcap - 1, i = (uint32_t)(hsh ^ (hsh >> 32)) & mask;
    while (L->table[i]) { uint32_t j = L->table[i] - 1; if (L->hashes[j] == hsh) return -1; i = (i + 1) & mask; }
    if (L->n >= L->cap) return -2;
    uint32_t j = L->n++; L->table[i] = j + 1; L->hashes[j] = hsh; memcpy(L->blobs + (size_t)j * RAMSZ, blob, RAMSZ);
    L->links[j].parent = parent; L->links[j].input = input; return j;
}
static const uint8_t INPUTS[16] = { 0x00, 0x01, 0x02, 0x03, 0x40, 0x41, 0x42, 0x43, 0x80, 0x81, 0x82, 0x83, 0xc0, 0xc1, 0xc2, 0xc3 };

int main(int argc, char **argv) {
    if (argc < 4) { fprintf(stderr, "usage: see header\n"); return 2; }
    const char *core = argv[1], *rom = argv[2], *inputs = argv[3], *outdir = "runs/bfs";
    long root = -1, layers = 400, mem_mb = 4000, input_skip = 0, workers = 8, deadline = -1, target_x = -1, max_speed = 40, accel = 2, margin = 0; int quiet_t = 0;
    for (int i = 4; i < argc; i++) {
        if (!strcmp(argv[i], "--root")) root = atol(argv[++i]); else if (!strcmp(argv[i], "--layers")) layers = atol(argv[++i]);
        else if (!strcmp(argv[i], "--mem-mb")) mem_mb = atol(argv[++i]); else if (!strcmp(argv[i], "--input-skip")) input_skip = atol(argv[++i]);
        else if (!strcmp(argv[i], "--workers")) workers = atol(argv[++i]); else if (!strcmp(argv[i], "--out")) outdir = argv[++i];
        else if (!strcmp(argv[i], "--deadline")) deadline = atol(argv[++i]); else if (!strcmp(argv[i], "--target-x")) target_x = atol(argv[++i]);
        else if (!strcmp(argv[i], "--max-speed")) max_speed = atol(argv[++i]); else if (!strcmp(argv[i], "--accel")) accel = atol(argv[++i]);
        else if (!strcmp(argv[i], "--margin")) margin = atol(argv[++i]); else if (!strcmp(argv[i], "--quiet-terminals")) quiet_t = 1;
        else { fprintf(stderr, "unknown option %s\n", argv[i]); return 2; }
    }
    if (root < 0) { fprintf(stderr, "--root required\n"); return 2; }
    void *h = dlopen(core, RTLD_NOW | RTLD_LOCAL); if (!h) { fprintf(stderr, "dlopen: %s\n", dlerror()); return 1; }
    ((void (*)(retro_environment_t))dlsym(h, "retro_set_environment"))(env_cb);
    ((void (*)(retro_video_refresh_t))dlsym(h, "retro_set_video_refresh"))(video_cb);
    ((void (*)(retro_audio_sample_t))dlsym(h, "retro_set_audio_sample"))(audio_cb);
    ((void (*)(retro_audio_sample_batch_t))dlsym(h, "retro_set_audio_sample_batch"))(audio_batch_cb);
    ((void (*)(retro_input_poll_t))dlsym(h, "retro_set_input_poll"))(input_poll_cb);
    ((void (*)(retro_input_state_t))dlsym(h, "retro_set_input_state"))(input_state_cb);
    ((void (*)(void))dlsym(h, "retro_init"))();
    c_run = dlsym(h, "retro_run"); c_ser = dlsym(h, "retro_serialize"); c_unser = dlsym(h, "retro_unserialize");
    FILE *f = fopen(inputs, "rb"); if (!f) { perror(inputs); return 1; }
    fseek(f, 0, SEEK_END); long nin = ftell(f); fseek(f, 0, SEEK_SET); uint8_t *in = malloc(nin); if (fread(in, 1, nin, f) != (size_t)nin) return 1; fclose(f);
    FILE *rf = fopen(rom, "rb"); if (!rf) { perror(rom); return 1; }
    fseek(rf, 0, SEEK_END); long rsz = ftell(rf); fseek(rf, 0, SEEK_SET); void *rdata = malloc(rsz); if (fread(rdata, 1, rsz, rf) != (size_t)rsz) return 1; fclose(rf);
    struct retro_game_info gi = { rom, rdata, (size_t)rsz, NULL };
    if (!((bool (*)(const struct retro_game_info *))dlsym(h, "retro_load_game"))(&gi)) { fprintf(stderr, "load failed\n"); return 1; }
    ram = ((void *(*)(unsigned))dlsym(h, "retro_get_memory_data"))(RETRO_MEMORY_SYSTEM_RAM);
    ssz = ((retro_serialize_size_t)dlsym(h, "retro_serialize_size"))();
    #define PAD(j) ((j) + input_skip < nin ? in[(j) + input_skip] : 0)
    for (long j = 0; j <= root; j++) { cur_pad = PAD(j); c_run(); }
    uint8_t *tmpl = malloc(ssz), *probe = malloc(ssz); c_ser(tmpl, ssz);
    { uint8_t s0 = ram[0x123]; ram[0x123] ^= 0xA5; c_ser(probe, ssz); ram[0x123] = s0;
      for (size_t i = 0; i < ssz; i++) if (probe[i] != tmpl[i]) { ram_off = (long)i - 0x123; break; }
      if (ram_off < 0 || memcmp(tmpl + ram_off, ram, RAMSZ)) { fprintf(stderr, "could not locate RAM in the savestate\n"); return 1; } }
    printf("root after frame %ld: GES=%u X=%u page=%u Y=%u speed=%d timer=%u%u%u; state %zu bytes, RAM at +%ld; workers %ld\n",
           root, ram[0x0e], ram[0x86], ram[0x6d], ram[0xce], (int8_t)ram[0x57], ram[0x7f8], ram[0x7f9], ram[0x7fa], ssz, ram_off, workers);
    if (deadline >= 0 && layers > deadline - root) layers = deadline - root;

    uint32_t cap = (uint32_t)(((size_t)mem_mb << 20) / 2 / (RAMSZ + 8 + sizeof(link_t) + 8));
    layer_t A, B; layer_init(&A, cap); layer_init(&B, cap); layer_t *cur = &A, *nxt = &B;
    layer_insert(cur, hash_ram(ram), ram, 0, 0);
    link_t **links = malloc((layers + 1) * sizeof(link_t *));
    const uint32_t PER_W = 2048;                       /* parents per worker per chunk */
    size_t arena_recs = (size_t)PER_W * 16, arena_bytes = arena_recs * sizeof(rec_t), term_max = 4096;
    rec_t **arenas = malloc(workers * sizeof(rec_t *)); uint32_t **counts = malloc(workers * sizeof(uint32_t *));
    term_t **terms = malloc(workers * sizeof(term_t *)); uint32_t **tcounts = malloc(workers * sizeof(uint32_t *)); long **stats = malloc(workers * sizeof(long *));
    for (long w = 0; w < workers; w++) {
        arenas[w] = mmap(NULL, arena_bytes, PROT_READ | PROT_WRITE, MAP_SHARED | MAP_ANONYMOUS, -1, 0);
        counts[w] = mmap(NULL, 4096, PROT_READ | PROT_WRITE, MAP_SHARED | MAP_ANONYMOUS, -1, 0);
        terms[w] = mmap(NULL, term_max * sizeof(term_t), PROT_READ | PROT_WRITE, MAP_SHARED | MAP_ANONYMOUS, -1, 0);
        tcounts[w] = (uint32_t *)((uint8_t *)counts[w] + 64); stats[w] = (long *)((uint8_t *)counts[w] + 128);
        if (arenas[w] == MAP_FAILED || counts[w] == MAP_FAILED || terms[w] == MAP_FAILED) { perror("mmap"); return 1; }
    }
    char path[1024]; snprintf(path, sizeof path, "%s/terminals.txt", outdir); FILE *tf = fopen(path, "w"); if (!tf) { perror(path); return 1; }
    long best_tset = -1, best_layer = -1; uint32_t best_idx = 0; uint8_t best_input = 0; long nterm = 0; double t0 = now();
    uint8_t *work = malloc(ssz); memcpy(work, tmpl, ssz);
    for (long L = 0; L < layers; L++) {
        layer_clear(nxt); long dup = 0, dead = 0, term = 0, full = 0, pruned = 0; double tl = now();
        long frames_left = deadline >= 0 ? deadline - (root + L + 1) : -1;
        for (uint32_t base = 0; base < cur->n; base += PER_W * workers) {
            long nw = 0;
            for (long w = 0; w < workers; w++) {
                uint32_t p0 = base + w * PER_W, p1 = p0 + PER_W; if (p0 >= cur->n) break; if (p1 > cur->n) p1 = cur->n; nw++;
                pid_t pid = fork();
                if (pid == 0) {
                    uint32_t nrec = 0, nt = 0; long s_dup = 0, s_dead = 0, s_pruned = 0; (void)s_dup;
                    for (uint32_t p = p0; p < p1; p++) {
                        const uint8_t *pr = cur->blobs + (size_t)p * RAMSZ;
                        for (int k = 0; k < 16; k++) {
                            memcpy(work + ram_off, pr, RAMSZ); c_unser(work, ssz); cur_pad = INPUTS[k]; c_run();
                            uint8_t ges = ram[0x0e];
                            if (ges == 4 || ges == 5) {
                                long fr = root + L + 1, grab = fr; uint8_t gy = ram[0xce], gx = ram[0x86];
                                int T = ram[0x7f8] * 100 + ram[0x7f9] * 10 + ram[0x7fa];
                                while (fr < grab + 1200 && ram[0x746] != 4) { fr++; cur_pad = 0; c_run(); }
                                if (nt < term_max) { term_t *t = &terms[w][nt++]; t->layer = L; t->grab = grab; t->tset = ram[0x746] == 4 ? fr : -1; t->T = T; t->ges = ges; t->y = gy; t->x = gx; t->input = INPUTS[k]; t->parent = p; }
                                continue;
                            }
                            if (ges == 6 || ges == 11 || ram[0xb5] > 1) { s_dead++; continue; }
                            if (deadline >= 0 && ges == 8) {
                                long xt = ((long)(ram[0x6d] << 8 | ram[0x86]) << 8) | ram[0x705]; long sp = (int8_t)ram[0x57], gain = 0;
                                for (long kk = 1; kk <= frames_left; kk++) { sp += accel; if (sp > max_speed) sp = max_speed; gain += 16 * sp; }
                                if (xt + gain + margin < target_x * 256) { s_pruned++; continue; }
                            }
                            rec_t *r = &arenas[w][nrec++]; r->hash = hash_ram(ram); r->parent = p; r->input = INPUTS[k]; memcpy(r->ram, ram, RAMSZ);
                        }
                    }
                    *counts[w] = nrec; *tcounts[w] = nt; stats[w][0] = s_dead; stats[w][1] = s_pruned; _exit(0);
                } else if (pid < 0) { perror("fork"); return 1; }
            }
            for (long w = 0; w < nw; w++) { int st; wait(&st); }
            for (long w = 0; w < nw; w++) {
                dead += stats[w][0]; pruned += stats[w][1];
                for (uint32_t i = 0; i < *counts[w]; i++) { rec_t *r = &arenas[w][i]; long rr = layer_insert(nxt, r->hash, r->ram, r->parent, r->input); if (rr == -1) dup++; else if (rr == -2) full++; }
                for (uint32_t i = 0; i < *tcounts[w]; i++) { term_t *t = &terms[w][i]; term++; nterm++;
                    if (!quiet_t || best_tset < 0 || t->tset < best_tset)
                        fprintf(tf, "layer %ld grab_after_frame %ld GES %u Y %u X %u T %d T_set %ld parent %u input %02x\n", t->layer, t->grab, t->ges, t->y, t->x, t->T, t->tset, t->parent, t->input);
                    if (t->tset >= 0 && (best_tset < 0 || t->tset < best_tset)) { best_tset = t->tset; best_layer = L; best_idx = t->parent; best_input = t->input; } }
            }
            if (full) break;
        }
        links[L] = malloc((size_t)nxt->n * sizeof(link_t)); memcpy(links[L], nxt->links, (size_t)nxt->n * sizeof(link_t));
        printf("layer %ld (after frame %ld): parents %u -> unique %u, dup %ld, dead %ld, pruned %ld, terminal %ld, full %ld; best T_set %ld; %.1fs (total %.0fs)\n",
               L + 1, root + L + 1, cur->n, nxt->n, dup, dead, pruned, term, full, best_tset, now() - tl, now() - t0);
        fflush(stdout); fflush(tf);
        if (full) { printf("LAYER FULL (cap %u states) — stop; raise --mem-mb\n", cap); break; }
        if (nxt->n == 0) { printf("no live states left\n"); break; }
        layer_t *t = cur; cur = nxt; nxt = t;
        if (best_tset >= 0 && L + 1 >= best_layer + 60) { printf("terminal found; stopping 60 layers after the best\n"); break; }
    }
    fclose(tf);
    printf("terminals: %ld; best T_set after frame %ld (layer %ld)\n", nterm, best_tset, best_layer);
    if (best_tset >= 0) {
        long npath = best_layer + 1; uint8_t *seq = malloc(npath); seq[best_layer] = best_input; uint32_t idx = best_idx;
        for (long L = best_layer - 1; L >= 0; L--) { seq[L] = links[L][idx].input; idx = links[L][idx].parent; }
        snprintf(path, sizeof path, "%s/best_inputs.bin", outdir); FILE *bf = fopen(path, "wb");
        for (long j = 0; j <= root; j++) fputc(PAD(j), bf); fwrite(seq, 1, npath, bf); fclose(bf);
        printf("wrote %s (%ld frames: movie to root, then %ld searched inputs)\n", path, root + 1 + npath, npath);
    }
    return 0;
}
