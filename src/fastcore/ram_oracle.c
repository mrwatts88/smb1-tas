/* P3.2 — RAM oracle: single-byte perturbation sweep on the QuickNES fast core (Track B).
 *
 *   ram_oracle CORE.so ROM.nes INPUTS.bin --at FRAME [--input-skip 2] [--addr-lo 0x5e0]
 *              [--addr-hi 0x6cf] [--values all|v1,v2,...] [--cap N] [--no-death-exit] [--out FILE]
 *
 * Method: run the movie to FRAME once, serialize.  For every (address, value) pair: unserialize,
 * poke ram[address] = value, then continue with the movie's own remaining inputs until one of
 *   VICTORY   OperMode ($0770) reaches 2 AND WorldNumber ($075F) >= 7 -> a real ending; compare
 *             its frame against the baseline's.  OperMode 2 alone is NOT an ending: VictoryMode is
 *             entered at every castle axe, and PlayerEndWorld only terminates when WorldNumber >= 7
 *             (otherwise it increments the world and returns to game mode).  An axe reached below
 *             world 8 is recorded in axe_frame and the run continues.
 *   CONVERGED the perturbed RAM hash equals the baseline hash for the same frame (absorbed;
 *             identical RAM => identical future under the same inputs, so it can never win early)
 *   DEAD      lives ($075A) dropped below baseline, or OperMode reached 3 (game over)
 *   CAP       the frame budget ran out (default: the baseline victory frame)
 * and record what the run reached.  The baseline RAM hash per frame is computed in-process in one
 * pass first, so the oracle needs no external dump and no row-origin bookkeeping.
 *
 * NOTE (assumption, documented in docs/experiments/P3.2-ram-oracle.md): DEAD exit assumes a run
 * that loses a life cannot then finish the game earlier than baseline while replaying the WR's own
 * remaining inputs.  Pass --no-death-exit to sweep without it.
 *
 * Output: CSV  addr,value,outcome,frames_run,victory_frame,max_opermode,max_world,areas
 * Only rows that did something (not CONVERGED-with-nothing-seen) are printed unless --all-rows.
 */
#include <dlfcn.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <libretro.h>

#define OPERMODE 0x770
#define WORLDNUM 0x75f
#define LIVES    0x75a
#define AREAPTR  0x750

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
static uint64_t fnv(const uint8_t *p, size_t n) {
    uint64_t h = 1469598103934665603ULL;
    for (size_t i = 0; i < n; i++) { h ^= p[i]; h *= 1099511628211ULL; }
    return h;
}

int main(int argc, char **argv) {
    if (argc < 4) {
        fprintf(stderr, "usage: %s CORE.so ROM.nes INPUTS.bin --at FRAME [--input-skip N] "
                        "[--addr-lo H] [--addr-hi H] [--values all|a,b,c] [--cap N] "
                        "[--no-death-exit] [--all-rows] [--out FILE]\n", argv[0]);
        return 2;
    }
    const char *core = argv[1], *rom = argv[2], *inputs = argv[3], *outpath = NULL;
    long at = -1, input_skip = 0, addr_lo = 0x5e0, addr_hi = 0x6cf, cap = -1;
    int death_exit = 1, all_rows = 0, probe = 0; long probe_n = 400;
    uint8_t vals[256]; int nvals = 0;
    for (int i = 4; i < argc; i++) {
        if (!strcmp(argv[i], "--at")) at = strtol(argv[++i], NULL, 0);
        else if (!strcmp(argv[i], "--input-skip")) input_skip = strtol(argv[++i], NULL, 0);
        else if (!strcmp(argv[i], "--addr-lo")) addr_lo = strtol(argv[++i], NULL, 0);
        else if (!strcmp(argv[i], "--addr-hi")) addr_hi = strtol(argv[++i], NULL, 0);
        else if (!strcmp(argv[i], "--cap")) cap = strtol(argv[++i], NULL, 0);
        else if (!strcmp(argv[i], "--no-death-exit")) death_exit = 0;
        else if (!strcmp(argv[i], "--all-rows")) all_rows = 1;
        else if (!strcmp(argv[i], "--probe")) probe = 1;
        else if (!strcmp(argv[i], "--probe-frames")) probe_n = strtol(argv[++i], NULL, 0);
        else if (!strcmp(argv[i], "--out")) outpath = argv[++i];
        else if (!strcmp(argv[i], "--values")) {
            const char *s = argv[++i];
            if (!strcmp(s, "all")) { for (int v = 0; v < 256; v++) vals[nvals++] = (uint8_t)v; }
            else { char *dup = strdup(s), *tok = strtok(dup, ",");
                   while (tok && nvals < 256) { vals[nvals++] = (uint8_t)strtol(tok, NULL, 0); tok = strtok(NULL, ","); }
                   free(dup); }
        } else { fprintf(stderr, "unknown option %s\n", argv[i]); return 2; }
    }
    if (at < 0) { fprintf(stderr, "--at FRAME is required\n"); return 2; }
    if (!nvals) { for (int v = 0; v < 256; v++) vals[nvals++] = (uint8_t)v; }

    void *h = dlopen(core, RTLD_NOW | RTLD_LOCAL);
    if (!h) { fprintf(stderr, "dlopen: %s\n", dlerror()); return 1; }
    SYM(retro_set_environment) SYM(retro_set_video_refresh) SYM(retro_set_audio_sample)
    SYM(retro_set_audio_sample_batch) SYM(retro_set_input_poll) SYM(retro_set_input_state)
    SYM(retro_init) SYM(retro_deinit) SYM(retro_load_game) SYM(retro_unload_game) SYM(retro_run)
    SYM(retro_serialize_size) SYM(retro_serialize) SYM(retro_unserialize)
    SYM(retro_get_memory_data) SYM(retro_get_memory_size)

    FILE *f = fopen(inputs, "rb"); if (!f) { perror(inputs); return 1; }
    fseek(f, 0, SEEK_END); long nin = ftell(f); fseek(f, 0, SEEK_SET);
    uint8_t *in = malloc(nin);
    if (fread(in, 1, nin, f) != (size_t)nin) { perror("read inputs"); return 1; }
    fclose(f);
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
    if (!ram || retro_get_memory_size(RETRO_MEMORY_SYSTEM_RAM) < 0x800) {
        fprintf(stderr, "no system RAM exposed\n"); return 1; }
    size_t ssz = retro_serialize_size();
    void *state = malloc(ssz);

    /* ---- pass 1: the baseline.  RAM hash per frame + the victory frame. ---- */
    long nframes = nin - input_skip;
    uint64_t *bhash = malloc(sizeof(uint64_t) * nframes);
    uint8_t *blives = malloc(nframes);
    long base_victory = -1;
    /* Route-progress table: each distinct (WorldNumber, AreaPointer) pair in order of first
     * appearance, with the baseline frame that first reached it.  A perturbed run that reaches
     * one of these pairs EARLIER than the baseline did has skipped ahead on the route — which is
     * worth frames even when the game does not end.  This is the "closer to the end" test. */
    #define MAXST 128
    static uint8_t st_w[MAXST], st_a[MAXST]; static long st_f[MAXST]; int nst = 0;
    /* Route-AGNOSTIC progress: the baseline frame at which each WorldNumber value is first reached.
     * Scores a skip that lands OFF the WR's itinerary entirely (a different world/level that may
     * still be faster overall) — which the (world,area) table above cannot see, since it only
     * knows states the WR itself visits. */
    long world_first[256]; { int k; for (k = 0; k < 256; k++) world_first[k] = -1; }
    for (long i = 0; i < nframes; i++) {
        cur_pad = in[i + input_skip];
        retro_run();
        bhash[i] = fnv(ram, 0x800);
        blives[i] = ram[LIVES];
        if (base_victory < 0 && ram[OPERMODE] == 2) base_victory = i;
        { int k, found = 0;
          for (k = 0; k < nst; k++) if (st_w[k] == ram[WORLDNUM] && st_a[k] == ram[AREAPTR]) { found = 1; break; }
          if (!found && nst < MAXST) { st_w[nst] = ram[WORLDNUM]; st_a[nst] = ram[AREAPTR]; st_f[nst] = i; nst++; } }
        if (world_first[ram[WORLDNUM]] < 0) world_first[ram[WORLDNUM]] = i;
        if (i == at) { if (!retro_serialize(state, ssz)) { fprintf(stderr, "serialize failed\n"); return 1; } }
    }
    if (base_victory < 0) { fprintf(stderr, "baseline never reached OperMode 2\n"); return 1; }
    if (at >= base_victory) { fprintf(stderr, "--at %ld is at/after the baseline victory %ld\n", at, base_victory); return 1; }
    long budget = cap > 0 ? cap : base_victory - at;
    fprintf(stderr, "baseline: %ld frames, victory at frame %ld (core origin); perturbing at %ld; "
                    "budget %ld frames/run; %ld addrs x %d values = %ld runs\n",
            nframes, base_victory, at, budget, addr_hi - addr_lo + 1, nvals,
            (addr_hi - addr_lo + 1) * (long)nvals);

    FILE *out = outpath ? fopen(outpath, "w") : stdout;
    if (!out) { perror(outpath); return 1; }
    fprintf(out, "# ram_oracle at=%ld baseline_victory=%ld budget=%ld death_exit=%d\n",
            at, base_victory, budget, death_exit);
    fprintf(stderr, "route table: %d distinct (world,area) states\n", nst);
    fprintf(out, "addr,value,outcome,frames_run,victory_frame,axe_frame,max_opermode,max_world,ahead_frames,ahead_state,world_ahead,world_ahead_n,new_areas\n");

    /* ---- probe mode: one (addr,value), per-frame diagnostics ---- */
    if (probe) {
        if (!retro_unserialize(state, ssz)) { fprintf(stderr, "unserialize failed\n"); return 1; }
        ram = (uint8_t *)retro_get_memory_data(RETRO_MEMORY_SYSTEM_RAM);
        ram[addr_lo] = vals[0];
        fprintf(out, "# probe addr=0x%lx value=%u at=%ld\n", addr_lo, vals[0], at);
        fprintf(out, "frame,diverged,opermode,world,frenzy_6cb,queue_6cd,eid0,eid1,eid2,eid3,eid4,eflag0..4\n");
        long first_eid = -1, first_div = -1;
        for (long j = 0; j < probe_n; j++) {
            long fi = at + 1 + j;
            if (fi + input_skip >= nin) break;
            cur_pad = in[fi + input_skip];
            retro_run();
            int div = fnv(ram, 0x800) != bhash[fi];
            if (div && first_div < 0) first_div = fi;
            for (int k = 0; k < 5; k++)
                if (ram[0x16 + k] == vals[0] && first_eid < 0) first_eid = fi;
            fprintf(out, "%ld,%d,%u,%u,%02x,%02x,%02x,%02x,%02x,%02x,%02x,%02x %02x %02x %02x %02x\n",
                    fi, div, ram[OPERMODE], ram[WORLDNUM], ram[0x6cb], ram[0x6cd],
                    ram[0x16], ram[0x17], ram[0x18], ram[0x19], ram[0x1a],
                    ram[0x0f], ram[0x10], ram[0x11], ram[0x12], ram[0x13]);
        }
        fprintf(stderr, "probe: first divergence frame %ld; first frame an Enemy_ID slot == 0x%02x: %ld\n",
                first_div, vals[0], first_eid);
        if (outpath) fclose(out);
        retro_unload_game(); retro_deinit(); dlclose(h);
        return 0;
    }

    double t0 = now(); long total_frames = 0, nrun = 0, njack = 0;
    for (long addr = addr_lo; addr <= addr_hi; addr++) {
        for (int vi = 0; vi < nvals; vi++) {
            if (!retro_unserialize(state, ssz)) { fprintf(stderr, "unserialize failed\n"); return 1; }
            ram = (uint8_t *)retro_get_memory_data(RETRO_MEMORY_SYSTEM_RAM);
            uint8_t orig = ram[addr];
            ram[addr] = vals[vi];
            int noop = (orig == vals[vi]);
            uint8_t max_om = 0, max_w = 0;
            uint8_t seen_area[256]; memset(seen_area, 0, sizeof seen_area);
            const char *outcome = "CAP"; long vf = -1, axef = -1, j = 0;
            long ahead = 0; int ahead_w = -1, ahead_a = -1; long wahead = 0; int wahead_w = -1;
            for (j = 0; j < budget; j++) {
                long fi = at + 1 + j;
                if (fi + input_skip >= nin) { outcome = "EOF"; break; }
                cur_pad = in[fi + input_skip];
                retro_run();
                uint8_t om = ram[OPERMODE];
                if (om > max_om) max_om = om;
                if (ram[WORLDNUM] > max_w) max_w = ram[WORLDNUM];
                seen_area[ram[AREAPTR]] = 1;
                if (world_first[ram[WORLDNUM]] >= 0 && world_first[ram[WORLDNUM]] - fi > wahead) {
                    wahead = world_first[ram[WORLDNUM]] - fi; wahead_w = ram[WORLDNUM]; }
                { int k; for (k = 0; k < nst; k++)
                    if (st_w[k] == ram[WORLDNUM] && st_a[k] == ram[AREAPTR]) {
                        if (st_f[k] - fi > ahead) { ahead = st_f[k] - fi; ahead_w = ram[WORLDNUM]; ahead_a = ram[AREAPTR]; }
                        break; } }
                /* OperMode 2 = VictoryMode, entered at EVERY castle axe (VictoryModeSubroutines:
                 * BridgeCollapse -> ... -> PlayerEndWorld).  Only PlayerEndWorld's `cpy #World8 /
                 * bcs` actually ends the game; below world 8 it increments WorldNumber and returns
                 * to game mode.  So a real ending needs WorldNumber >= 7 as well. */
                if (om == 2) {
                    if (ram[WORLDNUM] >= 7) { outcome = "VICTORY"; vf = fi; break; }
                    if (axef < 0) axef = fi;   /* an axe off-route: very interesting, keep running */
                }
                if (death_exit && (om == 3 || ram[LIVES] < blives[fi])) { outcome = "DEAD"; break; }
                if (fnv(ram, 0x800) == bhash[fi]) { outcome = "CONVERGED"; break; }
            }
            total_frames += j; nrun++;
            int interesting = strcmp(outcome, "CONVERGED") != 0 || max_om > 1 || axef >= 0 || ahead > 0 || wahead > 0 || j > 1;
            if (ahead > 0 || wahead > 0) njack++;
            if (!strcmp(outcome, "VICTORY") && vf >= 0 && vf < base_victory) njack++;
            if (all_rows || interesting || noop) {
                char areas[512]; int p = 0; areas[0] = 0;
                for (int a = 0; a < 256 && p < 500; a++)
                    if (seen_area[a]) p += snprintf(areas + p, sizeof areas - p, "%s%02x", p ? " " : "", a);
                fprintf(out, "0x%03lx,%u,%s%s,%ld,%ld,%ld,%u,%u,%ld,w%d/%02x,%ld,%d,%s\n", addr, vals[vi], outcome,
                        noop ? "(noop)" : "", j, vf, axef, max_om, max_w, ahead, ahead_w, ahead_a < 0 ? 0 : ahead_a,
                        wahead, wahead_w, areas);
            }
        }
        if ((addr - addr_lo) % 16 == 15) fflush(out);
    }
    double dt = now() - t0;
    fprintf(stderr, "done: %ld runs, %ld frames, %.1fs, %.0f fps, %ld earlier-victory hits\n",
            nrun, total_frames, dt, total_frames / dt, njack);
    if (outpath) fclose(out);
    retro_unload_game(); retro_deinit(); dlclose(h);
    return 0;
}
