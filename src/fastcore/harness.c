/* Headless libretro harness for SMB1 search work (P1.1).
 *
 *   harness CORE.so ROM.nes [INPUTS.bin] [options]
 *     --frames N        run at most N frames (default: length of INPUTS, or 600 without inputs)
 *     --ram OUT.ram     write the 2 KiB system RAM after every frame (frame-major, like the FCEUX dump)
 *     --reset0          call retro_reset() before frame 0 (fm2 movies with a reset command on frame 0)
 *     --input-skip N    feed input record N+j to frame j (boot alignment: QuickNES is 3 frames ahead of FCEUX)
 *     --state-every K   every K frames: retro_serialize + retro_unserialize (round-trip benchmark)
 *     --quiet           no per-run summary except the final line
 *   Input byte per frame: A=$01 B=$02 Select=$04 Start=$08 Up=$10 Down=$20 Left=$40 Right=$80.
 *   Prints frames, wall time, fps, state size and (if --state-every) save/load throughput.
 */
#include <dlfcn.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <libretro.h>

static uint8_t cur_pad;                 /* NES-order byte for the current frame */
static retro_environment_t dummy;

static void log_cb(enum retro_log_level level, const char *fmt, ...) { (void)level; (void)fmt; }
static struct retro_log_callback logcb = { log_cb };

static bool env_cb(unsigned cmd, void *data) {
    switch (cmd) {
    case RETRO_ENVIRONMENT_SET_PIXEL_FORMAT: return true;
    case RETRO_ENVIRONMENT_GET_CAN_DUPE: *(bool *)data = true; return true;
    case RETRO_ENVIRONMENT_GET_LOG_INTERFACE: *(struct retro_log_callback *)data = logcb; return true;
    case RETRO_ENVIRONMENT_GET_SYSTEM_DIRECTORY:
    case RETRO_ENVIRONMENT_GET_SAVE_DIRECTORY: *(const char **)data = "."; return true;
    case RETRO_ENVIRONMENT_SET_MEMORY_MAPS:
    case RETRO_ENVIRONMENT_SET_INPUT_DESCRIPTORS:
    case RETRO_ENVIRONMENT_SET_CONTROLLER_INFO:
    case RETRO_ENVIRONMENT_SET_GEOMETRY:
    case RETRO_ENVIRONMENT_SET_SUPPORT_NO_GAME: return true;
    case RETRO_ENVIRONMENT_GET_VARIABLE: {
        struct retro_variable *v = (struct retro_variable *)data;
        if (!strcmp(v->key, "quicknes_up_down_allowed")) { v->value = "enabled"; return true; }
        if (!strcmp(v->key, "quicknes_no_sprite_limit")) { v->value = "disabled"; return true; }
        return false;
    }
    case RETRO_ENVIRONMENT_GET_VARIABLE_UPDATE: *(bool *)data = false; return true;
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
    if (id == RETRO_DEVICE_ID_JOYPAD_MASK) {
        int16_t m = 0;
        if (p & 0x01) m |= 1 << RETRO_DEVICE_ID_JOYPAD_A;
        if (p & 0x02) m |= 1 << RETRO_DEVICE_ID_JOYPAD_B;
        if (p & 0x04) m |= 1 << RETRO_DEVICE_ID_JOYPAD_SELECT;
        if (p & 0x08) m |= 1 << RETRO_DEVICE_ID_JOYPAD_START;
        if (p & 0x10) m |= 1 << RETRO_DEVICE_ID_JOYPAD_UP;
        if (p & 0x20) m |= 1 << RETRO_DEVICE_ID_JOYPAD_DOWN;
        if (p & 0x40) m |= 1 << RETRO_DEVICE_ID_JOYPAD_LEFT;
        if (p & 0x80) m |= 1 << RETRO_DEVICE_ID_JOYPAD_RIGHT;
        return m;
    }
    switch (id) {
    case RETRO_DEVICE_ID_JOYPAD_A: return (p & 0x01) != 0;
    case RETRO_DEVICE_ID_JOYPAD_B: return (p & 0x02) != 0;
    case RETRO_DEVICE_ID_JOYPAD_SELECT: return (p & 0x04) != 0;
    case RETRO_DEVICE_ID_JOYPAD_START: return (p & 0x08) != 0;
    case RETRO_DEVICE_ID_JOYPAD_UP: return (p & 0x10) != 0;
    case RETRO_DEVICE_ID_JOYPAD_DOWN: return (p & 0x20) != 0;
    case RETRO_DEVICE_ID_JOYPAD_LEFT: return (p & 0x40) != 0;
    case RETRO_DEVICE_ID_JOYPAD_RIGHT: return (p & 0x80) != 0;
    default: return 0;
    }
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
typedef void (*retro_reset_t)(void);
typedef size_t (*retro_serialize_size_t)(void);
typedef bool (*retro_serialize_t)(void *, size_t);
typedef bool (*retro_unserialize_t)(const void *, size_t);
typedef void *(*retro_get_memory_data_t)(unsigned);
typedef size_t (*retro_get_memory_size_t)(unsigned);

static double now(void) { struct timespec t; clock_gettime(CLOCK_MONOTONIC, &t); return t.tv_sec + t.tv_nsec * 1e-9; }

int main(int argc, char **argv) {
    if (argc < 3) { fprintf(stderr, "usage: %s CORE.so ROM.nes [INPUTS.bin] [--frames N] [--ram OUT] [--reset0] [--state-every K] [--poke ADDR=VAL@FRAME]\n", argv[0]); return 2; }
    const char *core = argv[1], *rom = argv[2], *inputs = NULL, *ramout = NULL;
    long max_frames = -1, state_every = 0, input_skip = 0; int reset0 = 0, quiet = 0;
    /* --poke ADDR=VAL@FRAME : write one RAM byte after the given frame's retro_run().  Used to
       test "what if this flag were set here" questions (H49: WarpZoneControl mid pipe-descent). */
    long poke_addr[64], poke_val[64], poke_frame[64]; int npoke = 0;
    for (int i = 3; i < argc; i++) {
        if (!strcmp(argv[i], "--frames")) max_frames = atol(argv[++i]);
        else if (!strcmp(argv[i], "--ram")) ramout = argv[++i];
        else if (!strcmp(argv[i], "--reset0")) reset0 = 1;
        else if (!strcmp(argv[i], "--quiet")) quiet = 1;
        else if (!strcmp(argv[i], "--state-every")) state_every = atol(argv[++i]);
        else if (!strcmp(argv[i], "--input-skip")) input_skip = atol(argv[++i]);
        else if (!strcmp(argv[i], "--poke")) {
            if (npoke >= 64) { fprintf(stderr, "too many --poke\n"); return 2; }
            if (sscanf(argv[++i], "%li=%li@%li", &poke_addr[npoke], &poke_val[npoke], &poke_frame[npoke]) != 3) {
                fprintf(stderr, "bad --poke, want ADDR=VAL@FRAME\n"); return 2; }
            npoke++;
        }
        else if (argv[i][0] != '-') inputs = argv[i];
        else { fprintf(stderr, "unknown option %s\n", argv[i]); return 2; }
    }
    (void)dummy;
    void *h = dlopen(core, RTLD_NOW | RTLD_LOCAL);
    if (!h) { fprintf(stderr, "dlopen: %s\n", dlerror()); return 1; }
    SYM(retro_set_environment) SYM(retro_set_video_refresh) SYM(retro_set_audio_sample) SYM(retro_set_audio_sample_batch)
    SYM(retro_set_input_poll) SYM(retro_set_input_state) SYM(retro_init) SYM(retro_deinit) SYM(retro_load_game)
    SYM(retro_unload_game) SYM(retro_run) SYM(retro_reset) SYM(retro_serialize_size) SYM(retro_serialize)
    SYM(retro_unserialize) SYM(retro_get_memory_data) SYM(retro_get_memory_size)

    /* inputs */
    uint8_t *in = NULL; long nin = 0;
    if (inputs) {
        FILE *f = fopen(inputs, "rb"); if (!f) { perror(inputs); return 1; }
        fseek(f, 0, SEEK_END); nin = ftell(f); fseek(f, 0, SEEK_SET);
        in = malloc(nin); if (fread(in, 1, nin, f) != (size_t)nin) { perror("read"); return 1; } fclose(f);
    }
    long frames = max_frames >= 0 ? max_frames : (inputs ? nin - input_skip : 600);
    /* rom */
    FILE *rf = fopen(rom, "rb"); if (!rf) { perror(rom); return 1; }
    fseek(rf, 0, SEEK_END); long rsz = ftell(rf); fseek(rf, 0, SEEK_SET);
    void *rdata = malloc(rsz); if (fread(rdata, 1, rsz, rf) != (size_t)rsz) { perror("rom read"); return 1; } fclose(rf);

    retro_set_environment(env_cb);
    retro_set_video_refresh(video_cb); retro_set_audio_sample(audio_cb); retro_set_audio_sample_batch(audio_batch_cb);
    retro_set_input_poll(input_poll_cb); retro_set_input_state(input_state_cb);
    retro_init();
    struct retro_game_info gi = { rom, rdata, (size_t)rsz, NULL };
    if (!retro_load_game(&gi)) { fprintf(stderr, "retro_load_game failed\n"); return 1; }
    uint8_t *ram = retro_get_memory_data(RETRO_MEMORY_SYSTEM_RAM);
    size_t ramsz = retro_get_memory_size(RETRO_MEMORY_SYSTEM_RAM);
    if (!ram || ramsz < 0x800) { fprintf(stderr, "no system RAM exposed (%zu)\n", ramsz); return 1; }
    size_t ssz = retro_serialize_size();
    void *state = malloc(ssz);
    FILE *out = NULL;
    if (ramout) { out = fopen(ramout, "wb"); if (!out) { perror(ramout); return 1; } }
    if (reset0) retro_reset();

    double t0 = now(), tstate = 0; long nstates = 0;
    for (long i = 0; i < frames; i++) {
        cur_pad = (in && i + input_skip < nin) ? in[i + input_skip] : 0;
        retro_run();
        for (int k = 0; k < npoke; k++)
            if (i == poke_frame[k]) ram[poke_addr[k] & 0x7ff] = (uint8_t)poke_val[k];
        if (out) fwrite(ram, 1, 0x800, out);
        if (state_every && (i + 1) % state_every == 0) {
            double a = now();
            if (!retro_serialize(state, ssz)) { fprintf(stderr, "serialize failed at %ld\n", i); return 1; }
            if (!retro_unserialize(state, ssz)) { fprintf(stderr, "unserialize failed at %ld\n", i); return 1; }
            tstate += now() - a; nstates++;
        }
    }
    double dt = now() - t0;
    if (out) fclose(out);
    if (!quiet) {
        printf("frames=%ld wall=%.3fs fps=%.0f state_size=%zu", frames, dt, frames / dt, ssz);
        if (nstates) printf(" state_roundtrips=%ld roundtrip_us=%.1f", nstates, tstate / nstates * 1e6);
        printf(" ram[0x770]=%u ram[0x75f]=%u\n", ram[0x770], ram[0x75f]);
    }
    retro_unload_game(); retro_deinit(); dlclose(h);
    return 0;
}
