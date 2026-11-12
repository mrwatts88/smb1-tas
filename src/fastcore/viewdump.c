/* viewdump: replay a movie on the QuickNES core and keep the picture (route viewer, tools/route_viewer.py).
 *
 *   viewdump dump CORE ROM INPUTS.bin OUT_PREFIX [--input-skip N] [--reset0]
 *       writes OUT_PREFIX.ram    (2 KiB RAM after every frame, like harness --ram)
 *              OUT_PREFIX.frames (one 256x240 RGB565 picture per frame; overscan rows padded with 0)
 *   viewdump stitch OUT_PREFIX SEGFILE OUTDIR
 *       SEGFILE lines: "name first last" then, per frame f in [first,last], the camera is read from
 *       OUT_PREFIX.cam (int32 per frame = level-x of screen column 0 of the PICTURE of frame f, or -1
 *       to skip the frame). For every panorama pixel (rows 32..239, the status bar is not scrolled)
 *       the most common colour over all frames that show it is kept, so moving sprites vanish.
 *       Writes OUTDIR/name.rgb (raw RGB888) and prints "name width height".
 */
#include <dlfcn.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <libretro.h>

#define W 256
#define H 240
static uint8_t cur_pad;
static uint16_t pic[W * H];
static int got_w, got_h;

static void log_cb(enum retro_log_level level, const char *fmt, ...) { (void)level; (void)fmt; }
static struct retro_log_callback logcb = { log_cb };
static bool env_cb(unsigned cmd, void *data) {
    switch (cmd) {
    case RETRO_ENVIRONMENT_SET_PIXEL_FORMAT: return *(enum retro_pixel_format *)data == RETRO_PIXEL_FORMAT_RGB565;
    case RETRO_ENVIRONMENT_GET_CAN_DUPE: *(bool *)data = true; return true;
    case RETRO_ENVIRONMENT_GET_LOG_INTERFACE: *(struct retro_log_callback *)data = logcb; return true;
    case RETRO_ENVIRONMENT_GET_SYSTEM_DIRECTORY:
    case RETRO_ENVIRONMENT_GET_SAVE_DIRECTORY: *(const char **)data = "."; return true;
    case RETRO_ENVIRONMENT_SET_MEMORY_MAPS: case RETRO_ENVIRONMENT_SET_INPUT_DESCRIPTORS:
    case RETRO_ENVIRONMENT_SET_CONTROLLER_INFO: case RETRO_ENVIRONMENT_SET_GEOMETRY:
    case RETRO_ENVIRONMENT_SET_SUPPORT_NO_GAME: return true;
    case RETRO_ENVIRONMENT_GET_VARIABLE: {
        struct retro_variable *v = (struct retro_variable *)data;
        if (!strcmp(v->key, "quicknes_up_down_allowed")) { v->value = "enabled"; return true; }
        if (!strcmp(v->key, "quicknes_no_sprite_limit")) { v->value = "disabled"; return true; }
        if (!strcmp(v->key, "quicknes_use_overscan_v")) { v->value = "enabled"; return true; }
        if (!strcmp(v->key, "quicknes_use_overscan_h")) { v->value = "enabled"; return true; }
        return false;
    }
    case RETRO_ENVIRONMENT_GET_VARIABLE_UPDATE: *(bool *)data = false; return true;
    default: return false;
    }
}
static void video_cb(const void *d, unsigned w, unsigned h, size_t p) {
    if (!d) return;                                   /* dupe: keep the previous picture */
    got_w = w; got_h = h;
    int y0 = (H - (int)h) / 2, x0 = (W - (int)w) / 2;
    memset(pic, 0, sizeof pic);
    for (unsigned y = 0; y < h && y0 + (int)y < H; y++)
        memcpy(pic + (y0 + y) * W + x0, (const uint8_t *)d + y * p, (w < W ? w : W) * 2);
}
static void audio_cb(int16_t l, int16_t r) { (void)l; (void)r; }
static size_t audio_batch_cb(const int16_t *d, size_t n) { (void)d; return n; }
static void input_poll_cb(void) {}
static int16_t input_state_cb(unsigned port, unsigned dev, unsigned idx, unsigned id) {
    (void)idx;
    if (port != 0 || (dev & 0xff) != RETRO_DEVICE_JOYPAD) return 0;
    static const int map[8] = { RETRO_DEVICE_ID_JOYPAD_A, RETRO_DEVICE_ID_JOYPAD_B, RETRO_DEVICE_ID_JOYPAD_SELECT,
        RETRO_DEVICE_ID_JOYPAD_START, RETRO_DEVICE_ID_JOYPAD_UP, RETRO_DEVICE_ID_JOYPAD_DOWN,
        RETRO_DEVICE_ID_JOYPAD_LEFT, RETRO_DEVICE_ID_JOYPAD_RIGHT };
    if (id == RETRO_DEVICE_ID_JOYPAD_MASK) {
        int16_t m = 0;
        for (int b = 0; b < 8; b++) if (cur_pad & (1 << b)) m |= 1 << map[b];
        return m;
    }
    for (int b = 0; b < 8; b++) if ((int)id == map[b]) return (cur_pad >> b) & 1;
    return 0;
}

#define SYM(name) name##_t name = (name##_t)dlsym(h, #name); if (!name) { fprintf(stderr, "missing %s\n", #name); return 1; }
typedef void (*retro_set_environment_t)(retro_environment_t);
typedef void (*retro_set_video_refresh_t)(retro_video_refresh_t);
typedef void (*retro_set_audio_sample_t)(retro_audio_sample_t);
typedef void (*retro_set_audio_sample_batch_t)(retro_audio_sample_batch_t);
typedef void (*retro_set_input_poll_t)(retro_input_poll_t);
typedef void (*retro_set_input_state_t)(retro_input_state_t);
typedef void (*retro_init_t)(void);
typedef bool (*retro_load_game_t)(const struct retro_game_info *);
typedef void (*retro_run_t)(void);
typedef void (*retro_reset_t)(void);
typedef void *(*retro_get_memory_data_t)(unsigned);

static uint8_t *slurp(const char *path, long *n) {
    FILE *f = fopen(path, "rb"); if (!f) { perror(path); exit(1); }
    fseek(f, 0, SEEK_END); *n = ftell(f); fseek(f, 0, SEEK_SET);
    uint8_t *b = malloc(*n); if (fread(b, 1, *n, f) != (size_t)*n) { perror("read"); exit(1); } fclose(f);
    return b;
}

static int do_dump(int argc, char **argv) {
    if (argc < 6) { fprintf(stderr, "usage: viewdump dump CORE ROM INPUTS OUT_PREFIX [--input-skip N] [--reset0]\n"); return 2; }
    const char *core = argv[2], *rom = argv[3], *inputs = argv[4], *pre = argv[5];
    long skip = 0; int reset0 = 0;
    for (int i = 6; i < argc; i++) {
        if (!strcmp(argv[i], "--input-skip")) skip = atol(argv[++i]);
        else if (!strcmp(argv[i], "--reset0")) reset0 = 1;
        else { fprintf(stderr, "unknown option %s\n", argv[i]); return 2; }
    }
    void *h = dlopen(core, RTLD_NOW | RTLD_LOCAL);
    if (!h) { fprintf(stderr, "dlopen: %s\n", dlerror()); return 1; }
    SYM(retro_set_environment) SYM(retro_set_video_refresh) SYM(retro_set_audio_sample) SYM(retro_set_audio_sample_batch)
    SYM(retro_set_input_poll) SYM(retro_set_input_state) SYM(retro_init) SYM(retro_load_game) SYM(retro_run)
    SYM(retro_reset) SYM(retro_get_memory_data)
    long nin, rsz; uint8_t *in = slurp(inputs, &nin), *rdata = slurp(rom, &rsz);
    retro_set_environment(env_cb);
    retro_set_video_refresh(video_cb); retro_set_audio_sample(audio_cb); retro_set_audio_sample_batch(audio_batch_cb);
    retro_set_input_poll(input_poll_cb); retro_set_input_state(input_state_cb);
    retro_init();
    struct retro_game_info gi = { rom, rdata, (size_t)rsz, NULL };
    if (!retro_load_game(&gi)) { fprintf(stderr, "retro_load_game failed\n"); return 1; }
    uint8_t *ram = retro_get_memory_data(RETRO_MEMORY_SYSTEM_RAM);
    char p1[1024], p2[1024];
    snprintf(p1, sizeof p1, "%s.ram", pre); snprintf(p2, sizeof p2, "%s.frames", pre);
    FILE *fr = fopen(p1, "wb"), *ff = fopen(p2, "wb");
    if (!fr || !ff) { perror("open out"); return 1; }
    if (reset0) retro_reset();
    long frames = nin - skip;
    for (long i = 0; i < frames; i++) {
        cur_pad = in[i + skip];
        retro_run();
        fwrite(ram, 1, 0x800, fr);
        fwrite(pic, 2, W * H, ff);
    }
    fclose(fr); fclose(ff);
    printf("frames=%ld picture=%dx%d\n", frames, got_w, got_h);
    return 0;
}

/* stitch ------------------------------------------------------------------------------------- */
#define Y0 32
#define PH (H - Y0)
#define NC 64
static int do_stitch(int argc, char **argv) {
    if (argc < 5) { fprintf(stderr, "usage: viewdump stitch OUT_PREFIX SEGFILE OUTDIR\n"); return 2; }
    const char *pre = argv[2], *seg = argv[3], *outdir = argv[4];
    char path[1024];
    snprintf(path, sizeof path, "%s.cam", pre);
    long ncb; int32_t *cam = (int32_t *)slurp(path, &ncb); long nf = ncb / 4;
    snprintf(path, sizeof path, "%s.frames", pre);
    FILE *ff = fopen(path, "rb"); if (!ff) { perror(path); return 1; }
    FILE *sf = fopen(seg, "r"); if (!sf) { perror(seg); return 1; }
    char name[256]; long a, b;
    static uint16_t fr[W * H];
    while (fscanf(sf, "%255s %ld %ld", name, &a, &b) == 3) {
        int lo = 1 << 30, hi = -1;
        for (long f = a; f <= b && f < nf; f++) if (cam[f] >= 0) {
            if (cam[f] + 8 < lo) lo = cam[f] + 8;
            if (cam[f] + W > hi) hi = cam[f] + W;
        }
        if (hi < 0) { printf("%s 0 0\n", name); continue; }
        int pw = hi - lo;
        uint16_t pal[NC]; int npal = 0;
        uint16_t *cnt = calloc((size_t)pw * PH * NC, 2);
        if (!cnt) { fprintf(stderr, "oom\n"); return 1; }
        for (long f = a; f <= b && f < nf; f++) {
            if (cam[f] < 0) continue;
            fseeko(ff, (off_t)f * W * H * 2, SEEK_SET);
            if (fread(fr, 2, W * H, ff) != W * H) { fprintf(stderr, "short frames file\n"); return 1; }
            for (int y = Y0; y < H; y++) for (int x = 8; x < W; x++) {
                uint16_t c = fr[y * W + x]; int k;
                for (k = 0; k < npal && pal[k] != c; k++) ;
                if (k == npal) { if (npal == NC) k = NC - 1; else pal[npal++] = c; }
                int X = cam[f] + x - lo;
                uint16_t *q = &cnt[((size_t)(y - Y0) * pw + X) * NC + k];
                if (*q < 65535) (*q)++;
            }
        }
        snprintf(path, sizeof path, "%s/%s.rgb", outdir, name);
        FILE *o = fopen(path, "wb"); if (!o) { perror(path); return 1; }
        uint8_t *row = malloc(pw * 3);
        for (int y = 0; y < PH; y++) {
            for (int X = 0; X < pw; X++) {
                uint16_t *q = &cnt[((size_t)y * pw + X) * NC]; int best = 0;
                for (int k = 1; k < npal; k++) if (q[k] > q[best]) best = k;
                uint16_t c = q[best] ? pal[best] : 0;
                int r = (c >> 11) & 31, g = (c >> 5) & 63, bl = c & 31;
                row[X * 3] = (r << 3) | (r >> 2); row[X * 3 + 1] = (g << 2) | (g >> 4); row[X * 3 + 2] = (bl << 3) | (bl >> 2);
            }
            fwrite(row, 1, pw * 3, o);
        }
        fclose(o); free(row); free(cnt);
        printf("%s %d %d %d colours=%d\n", name, pw, PH, lo, npal);
        fflush(stdout);
    }
    return 0;
}

int main(int argc, char **argv) {
    if (argc >= 2 && !strcmp(argv[1], "dump")) return do_dump(argc, argv);
    if (argc >= 2 && !strcmp(argv[1], "stitch")) return do_stitch(argc, argv);
    fprintf(stderr, "usage: viewdump dump|stitch ... (see header)\n");
    return 2;
}
