/* Find where the 2 KiB system RAM lives inside the core's serialized state, and test whether a state can
 * be reconstructed from RAM alone + a template blob (P2.1b compact-state experiment).
 *   state_probe CORE ROM INPUTS --input-skip 2 --frame-a A --frame-b B --run N
 * Runs the movie to frame A (template) and to frame B (test); builds blob' = template with the RAM region
 * replaced by B's RAM, unserializes blob', runs N frames with the movie inputs and compares the RAM trace
 * with the true continuation from B. Prints the RAM offset and the first differing frame (or MATCH).
 */
#include <dlfcn.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <libretro.h>
static uint8_t cur_pad;
static bool env_cb(unsigned cmd, void *data) {
    switch (cmd) {
    case RETRO_ENVIRONMENT_SET_PIXEL_FORMAT: return true;
    case RETRO_ENVIRONMENT_GET_CAN_DUPE: *(bool *)data = true; return true;
    case RETRO_ENVIRONMENT_GET_SYSTEM_DIRECTORY: case RETRO_ENVIRONMENT_GET_SAVE_DIRECTORY: *(const char **)data = "."; return true;
    case RETRO_ENVIRONMENT_GET_VARIABLE: { struct retro_variable *v = data;
        if (!strcmp(v->key, "quicknes_up_down_allowed")) { v->value = "enabled"; return true; } return false; }
    case RETRO_ENVIRONMENT_GET_VARIABLE_UPDATE: *(bool *)data = false; return true;
    case RETRO_ENVIRONMENT_SET_MEMORY_MAPS: case RETRO_ENVIRONMENT_SET_INPUT_DESCRIPTORS: case RETRO_ENVIRONMENT_SET_GEOMETRY: return true;
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
typedef void (*vfn)(void);
int main(int argc, char **argv) {
    const char *core = argv[1], *rom = argv[2], *inputs = argv[3]; long skip = 0, fa = 0, fb = 0, nrun = 300;
    for (int i = 4; i < argc; i++) {
        if (!strcmp(argv[i], "--input-skip")) skip = atol(argv[++i]); else if (!strcmp(argv[i], "--frame-a")) fa = atol(argv[++i]);
        else if (!strcmp(argv[i], "--frame-b")) fb = atol(argv[++i]); else if (!strcmp(argv[i], "--run")) nrun = atol(argv[++i]); }
    void *h = dlopen(core, RTLD_NOW | RTLD_LOCAL); if (!h) { fprintf(stderr, "%s\n", dlerror()); return 1; }
    void (*set_env)(retro_environment_t) = dlsym(h, "retro_set_environment");
    void (*set_video)(retro_video_refresh_t) = dlsym(h, "retro_set_video_refresh");
    void (*set_audio)(retro_audio_sample_t) = dlsym(h, "retro_set_audio_sample");
    void (*set_audio_b)(retro_audio_sample_batch_t) = dlsym(h, "retro_set_audio_sample_batch");
    void (*set_poll)(retro_input_poll_t) = dlsym(h, "retro_set_input_poll");
    void (*set_state)(retro_input_state_t) = dlsym(h, "retro_set_input_state");
    vfn init = dlsym(h, "retro_init"), run = dlsym(h, "retro_run");
    bool (*load)(const struct retro_game_info *) = dlsym(h, "retro_load_game");
    size_t (*ssize)(void) = dlsym(h, "retro_serialize_size");
    bool (*ser)(void *, size_t) = dlsym(h, "retro_serialize"); bool (*unser)(const void *, size_t) = dlsym(h, "retro_unserialize");
    void *(*memdata)(unsigned) = dlsym(h, "retro_get_memory_data");
    FILE *f = fopen(inputs, "rb"); fseek(f, 0, SEEK_END); long nin = ftell(f); fseek(f, 0, SEEK_SET); uint8_t *in = malloc(nin); if (fread(in, 1, nin, f) != (size_t)nin) return 1; fclose(f);
    FILE *rf = fopen(rom, "rb"); fseek(rf, 0, SEEK_END); long rsz = ftell(rf); fseek(rf, 0, SEEK_SET); void *rd = malloc(rsz); if (fread(rd, 1, rsz, rf) != (size_t)rsz) return 1; fclose(rf);
    set_env(env_cb); set_video(video_cb); set_audio(audio_cb); set_audio_b(audio_batch_cb); set_poll(input_poll_cb); set_state(input_state_cb); init();
    struct retro_game_info gi = { rom, rd, (size_t)rsz, NULL }; if (!load(&gi)) return 1;
    uint8_t *ram = memdata(RETRO_MEMORY_SYSTEM_RAM); size_t ssz = ssize();
    #define PAD(j) ((j) + skip < nin ? in[(j) + skip] : 0)
    uint8_t *blobA = malloc(ssz), *blobB = malloc(ssz), *blobT = malloc(ssz), *ramB = malloc(0x800);
    long fr = 0;
    for (; fr <= fa; fr++) { cur_pad = PAD(fr); run(); }
    ser(blobA, ssz);
    /* locate RAM: flip a byte in RAM, re-serialize, diff */
    uint8_t *probe = malloc(ssz); uint8_t save0 = ram[0x123]; ram[0x123] ^= 0xA5; ser(probe, ssz); ram[0x123] = save0;
    long off = -1; for (size_t i = 0; i < ssz; i++) if (probe[i] != blobA[i]) { off = (long)i - 0x123; break; }
    printf("state size %zu; RAM $0000 at blob offset %ld (check: blob[off+0x123] == ram? %d)\n", ssz, off, blobA[off + 0x123] == save0);
    for (; fr <= fb; fr++) { cur_pad = PAD(fr); run(); }
    ser(blobB, ssz); memcpy(ramB, ram, 0x800);
    /* true continuation */
    uint8_t *trace = malloc((size_t)nrun * 0x800);
    for (long k = 0; k < nrun; k++) { cur_pad = PAD(fb + 1 + k); run(); memcpy(trace + k * 0x800, ram, 0x800); }
    /* template reconstruction: A's blob with B's RAM */
    memcpy(blobT, blobA, ssz); memcpy(blobT + off, ramB, 0x800);
    if (!unser(blobT, ssz)) { printf("unserialize of template blob failed\n"); return 1; }
    long bad = -1; int nb = 0;
    for (long k = 0; k < nrun; k++) { cur_pad = PAD(fb + 1 + k); run();
        if (memcmp(trace + k * 0x800, ram, 0x800)) { if (bad < 0) bad = k; nb++; } }
    if (bad < 0) printf("MATCH: template(frame %ld)+RAM(frame %ld) reproduces %ld frames of the true continuation\n", fa, fb, nrun);
    else { printf("MISMATCH at continuation frame %ld (%d of %ld frames differ); first diff bytes:", bad, nb, nrun);
        memcpy(blobT, blobA, ssz); memcpy(blobT + off, ramB, 0x800); unser(blobT, ssz);
        for (long k = 0; k <= bad; k++) { cur_pad = PAD(fb + 1 + k); run(); }
        int c = 0; for (int i = 0; i < 0x800 && c < 10; i++) if (trace[bad * 0x800 + i] != ram[i]) { printf(" $%03X:%u/%u", i, trace[bad * 0x800 + i], ram[i]); c++; } printf("\n"); }
    /* also: how many bytes of the blob differ between A and B outside RAM? */
    long nd = 0; for (size_t i = 0; i < ssz; i++) if ((long)i < off || (long)i >= off + 0x800) if (blobA[i] != blobB[i]) nd++;
    printf("non-RAM blob bytes differing between frames %ld and %ld: %ld of %zu\n", fa, fb, nd, ssz - 0x800);
    return 0;
}
