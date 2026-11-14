/* Track E — the finder: archive-based exploration (Go-Explore) on the QuickNES fast core.
 *
 *   explore CORE.so ROM.nes INPUTS.bin --root FRAME [options]
 *
 * Why this shape.  Every search this project has run is a layered BFS or a beam, and both are
 * per-layer first-arrival gates: a manoeuvre that must PAY before it GAINS has worsening h and
 * dies on the layers it must survive (H39/F128).  An archive has no layers.  A state is stored
 * under a coarse CELL key (position, speed, scroll, room, enemy phase), the best-per-cell is
 * kept, and any cell can be resumed at any time — so a state that paid keeps its own cell and
 * stays reachable forever.  It is `--beam-buckets` without the layer.
 *
 * It runs on the REAL emulator, so there is no model-gap class (F147/F149/F150) and every path
 * it emits is core-verified by construction.
 *
 * Objective is the LAST INPUT frame, not the victory frame: a movie's length is measured to its
 * last input (F17), so a later ending with a longer input-free coast is a strict win.  Every
 * goal path is therefore tail-trimmed (the `--truncate` experiment of F223, run automatically).
 *
 * Options:
 *   --root N          run the movie's own inputs to core frame N, then explore from there
 *   --input-skip N    input record N+j feeds frame j (2 for this project's fm2, F45)
 *   --cells N         archive capacity (default 150000; ~13 KB state + path slot each)
 *   --rollout A,B     rollout length sampled uniformly in [A,B] (default 8,64)
 *   --horizon N       abandon a rollout N frames past the root (default 900)
 *   --coast N         zero frames appended when testing a trim (default 400)
 *   --no-seed-wr      do NOT seed the archive with the movie's own continuation
 *   --tournp P        probability of tournament (progress-biased) cell selection (default 0.75)
 *   --xcell/--ycell/--scell/--spdcell/--enemycell N   cell coarseness (px / px / px / speed / px)
 *   --subcell/--ysubcell N   key on the POSITION subpixels $0400/$0416 (F297; before 2026-11-07
 *                     these read the speed fractions $0705/$0433)
 *   --frccell/--yfrccell N   key on the speed fractions $0705/$0433 (the pre-F297 behaviour)
 *   --keyaddr ADDR[/DIV]     add RAM byte ADDR (divided by DIV) to the key; up to 4
 *   --no-ges-death    pre-F300 behaviour: a rollout only counts as dead when a life is lost, so
 *                     the death animation (GES 11) is archived as live cells
 *   --seed N, --secs N, --report N, --out DIR
 *
 * Path file: a text header line then `len` raw input bytes.  Replay = movie's own inputs to
 * --root, then these.
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
#define GES      0x0e
#define PX       0x86
#define PPAGE    0x6d
#define PY       0xce
#define PYHI     0xb5
#define PXSPD    0x57
#define PSTATE   0x1d
#define SLX      0x71c
#define SLPAGE   0x71a
#define SCTIMER  0x785
/* F297 (2026-11-07): $0705/$0433 are SPEED fractions (Player_X_MoveForce = friction/subspeed
   accumulator, Player_Y_MoveForce = vertical-speed fraction). The POSITION subpixels are
   SprObject_X_MoveForce $0400 and SprObject_YMF_Dummy $0416. --subcell/--ysubcell now key on
   the position subpixels; --frccell/--yfrccell key on the speed fractions (the old behaviour). */
#define PXSUB    0x400   /* SprObject_X_MoveForce - horizontal position subpixel */
#define PYSUB    0x416   /* SprObject_YMF_Dummy - vertical position subpixel */
#define PXFRAC   0x705   /* Player_X_MoveForce - horizontal speed fraction */
#define PYFRAC   0x433   /* Player_Y_MoveForce - vertical speed fraction */
#define ENID     0x16
#define ENFLAG   0x0f   /* Enemy_Flag: slot i is a live object iff $0f+i != 0 */
#define ENX      0x87

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
static void video_cb(const void *d, unsigned w, unsigned h, size_t p) { (void)d;(void)w;(void)h;(void)p; }
static void audio_cb(int16_t l, int16_t r) { (void)l; (void)r; }
static size_t audio_batch_cb(const int16_t *d, size_t n) { (void)d; return n; }
static void input_poll_cb(void) {}
static int16_t input_state_cb(unsigned port, unsigned dev, unsigned idx, unsigned id) {
    (void)idx;
    if (port != 0 || (dev & 0xff) != RETRO_DEVICE_JOYPAD) return 0;
    uint8_t p = cur_pad;
    static const int map[9] = { 0x02, 0, 0x04, 0x08, 0x10, 0x20, 0x40, 0x80, 0x01 };
    if (id == RETRO_DEVICE_ID_JOYPAD_MASK) {
        int16_t m = 0;
        for (int i = 0; i < 9; i++) if (map[i] && (p & map[i])) m |= 1 << i;
        return m;
    }
    return id < 9 && map[id] && (p & map[id]) ? 1 : 0;
}
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
#define SYM(n) g_##n = (n##_t)dlsym(h, #n); if (!g_##n) { fprintf(stderr, "missing %s\n", #n); return 1; }

static retro_run_t g_retro_run; static retro_serialize_t g_retro_serialize;
static retro_unserialize_t g_retro_unserialize; static retro_get_memory_data_t g_retro_get_memory_data;
static retro_serialize_size_t g_retro_serialize_size;
static uint8_t *g_root_state; static size_t g_ssz; static uint8_t g_lives0;
#define RAMP() ((uint8_t *)g_retro_get_memory_data(RETRO_MEMORY_SYSTEM_RAM))
static long g_gaddr[8], g_gval[8]; static int g_ngoal=0;
static long g_raddr[8], g_rval[8]; static int g_nreq=0;
/* A state that already violates a required invariant can never satisfy the goal (the area
 * parser only moves forward, so AreaPointer never flips back).  Do not archive it. */
static inline int req_ok(const uint8_t *r){
    for(int i=0;i<g_nreq;i++) if(r[g_raddr[i]]!=(uint8_t)g_rval[i]) return 0;
    return 1;
}
static inline int goal_hit(const uint8_t *r){
    if(!g_ngoal) return r[OPERMODE]==2 && r[WORLDNUM]>=7;
    for(int i=0;i<g_ngoal;i++) if(r[g_gaddr[i]]!=(uint8_t)g_gval[i]) return 0;
    return 1;
}

static double now(void){ struct timespec t; clock_gettime(CLOCK_MONOTONIC,&t); return t.tv_sec+t.tv_nsec*1e-9; }
static uint64_t rngs = 88172645463325252ULL;
static inline uint64_t rnd(void){ rngs^=rngs<<13; rngs^=rngs>>7; rngs^=rngs<<17; return rngs*2685821657736338717ULL; }
static inline uint32_t rndn(uint32_t n){ return (uint32_t)(rnd() % n); }

/* replay `path` from the root state; return the frame index at victory, or -1 */
static long replay_victory(const uint8_t *path, long n, long root) {
    if (!g_retro_unserialize(g_root_state, g_ssz)) return -1;
    uint8_t *r = RAMP();
    for (long i = 0; i < n; i++) {
        cur_pad = path[i]; g_retro_run(); r = RAMP();
        if (r[LIVES] < g_lives0 || r[OPERMODE] == 3) return -1;
        if (goal_hit(r)) return root + i;
    }
    return -1;
}

/* F223's --truncate experiment, run automatically on every goal path: zero the tail from index c
 * onward (padding with `coast` more blank frames) and find the smallest c that still reaches the
 * axe.  Returns the last-input frame, or -1.  `wr_last` is the last input before the root. */
static long trim_path(const uint8_t *path, long plen, long root, long coast, long wr_last, long *out_cut, long limit) {
    long last = -1; for (long q = 0; q < plen; q++) if (path[q]) last = q;
    if (last < 0) return wr_last;
    uint8_t *buf = malloc(plen + coast);
    long bestc = last + 1, fails = 0;
    if (limit > 0) {   /* cheap gate: can the tail be cut at all past the incumbent? */
        long c0 = limit - root; if (c0 < 0) c0 = 0; if (c0 > last) c0 = last;
        memcpy(buf, path, c0); memset(buf + c0, 0, plen + coast - c0);
        if (replay_victory(buf, plen + coast, root) < 0) { free(buf); if(out_cut) *out_cut=last+1;
            long li0 = wr_last; for (long q = 0; q <= last; q++) if (path[q]) li0 = root + q; return li0; }
        bestc = c0; last = c0;
    }
    for (long c = last; c >= 0 && fails < 48; c--) {
        memcpy(buf, path, c); memset(buf + c, 0, plen + coast - c);
        if (replay_victory(buf, plen + coast, root) >= 0) { bestc = c; fails = 0; }
        else fails++;
    }
    free(buf);
    long li = wr_last; for (long q = 0; q < bestc; q++) if (path[q]) li = root + q;
    if (out_cut) *out_cut = bestc;
    return li;
}

/* P3.4 novelty sweep: states the game should never reach.  Each is a known glitch class or the
 * doorway to one -- Mario off the world, an out-of-table enemy id (the JumpEngine OOB of H43), a
 * non-zero frenzy buffer, a world/area/mode the level cannot legitimately produce, an
 * over-filled VRAM buffer (F218/F234).  Returns a bit mask; 0 = ordinary. */
static const char *ANOM_NAME[] = {
    "Y above world", "GES", "OperMode", "WorldNumber", "AreaPointer", "Enemy_ID out of table",
    "EnemyFrenzyBuffer", "VRAM_Buffer1_Offset", "Player_State", "PlayerSize",
    "WarpZoneControl", "AltEntranceControl", "ScrollLock", "EnemyFrenzyQueue",
    "SecondaryHardMode", "DuplicateObj_Offset", "position jump (clip/teleport)",
    "Enemy_ID novel in a live slot", "StarFlagObject in a slot", "stompable enemy at the flagpole",
    "ahead of the cap line (1/16 px)", "single-frame step over 40/16 px" };
#define NANOM 22
/* Self-calibrating: the allowed value sets are collected from the WR's OWN line through this same
 * region during --seed-wr, so "anomaly" means "a state the reference movie never produces here"
 * rather than a hand-guessed predicate.  Without --seed-wr only the absolute predicates fire. */
static uint8_t ok_ges[256], ok_oper[256], ok_world[256], ok_area[256], ok_pstate[256], ok_size[256];
static uint8_t ok_wzc[256], ok_alt[256], ok_lock[256], ok_enid[256];
static int g_calibrating=1;   /* learn from the root + the WR line before judging anything */
static int ok_nstarflag=0;    /* how many StarFlagObject slots the reference line ever holds here */
/* Class 19 (L10b): a live stompable enemy (id < $15, or a bullet bill $08/$33) within 80 px left /
 * 16 px right of the live FlagpoleFlagObject ($30), on screen.  That is the WR's own 8-2 ending (a
 * bullet-bill bounce into the glitch grab, core 12468-12472) and what 8-3 lacks (H57).  Calibrated:
 * if the reference line ever has it from this root, the class is off.  value = the enemy's id. */
/* Class 20 (N10): Mario further right than the reference movie was on the SAME frame, in the same
 * area, both in control.  Where the reference runs at the speed cap (4-1, 8-1, 8-3 after the start
 * ramp, F225) any lead at all is an over-cap displacement (H47) -- the one ingredient every near-miss
 * on the board lacks (F316 9/16 px, F318 1/4 px, F324 1/8 px, F334 11/16 px).  Where the reference
 * waits on purpose (4-2 mint, 1-2 clip) a lead is ordinary.  value = lead in 1/16 px, capped at 255;
 * g_maxlead tracks the largest lead and where. */
#define REFN 8192
static long g_refx[REFN]; static uint32_t g_refarea[REFN]; static long g_root_f=0, g_curf=0;
static long g_maxlead=0, g_maxlead_f=0, g_maxlead40=0, g_maxlead40_f=0; static uint8_t g_ref40[REFN];
static inline long x16_of(const uint8_t *r){ return (((long)r[0x6d]<<8)|r[0x86])*16 + (r[0x400]>>4); }
static inline uint32_t area_of(const uint8_t *r){ return ((uint32_t)r[0x75f]<<24)|((uint32_t)r[0x75c]<<16)|((uint32_t)r[0x760]<<8)|r[0x752]; }
static int ok_pole_enemy=0;
static inline int pole_enemy(const uint8_t *r, uint8_t *id){
    long px=-1;
    for(int q=0;q<6;q++) if(r[ENFLAG+q] && r[ENID+q]==0x30) px=(long)r[0x6e + q]*256+r[0x87 + q];
    if(px<0) return 0;
    for(int q=0;q<6;q++){ uint8_t e=r[ENID+q];
        if(!r[ENFLAG+q] || !(e<0x15 || e==0x33) || r[0xb6 + q]!=1) continue;
        long ex=(long)r[0x6e + q]*256+r[0x87 + q];
        if(ex>=px-80 && ex<=px+16){ *id=e; return 1; } }
    return 0;
}
static inline void anom_learn(const uint8_t *r){
    { long i_=g_curf-g_root_f; if(i_>=0 && i_<REFN){ g_refarea[i_]=area_of(r);
        /* g_refx = the CAP LINE, not the movie: the furthest the movie could be on this frame had it run
         * at 40/16 px per frame from its own best earlier position in this area.  The movie slows on
         * purpose in places (8-1 before the pole), and a lead over the movie there is ordinary.  The line
         * is carried through frames where the movie is not in control or is above the screen, so a
         * slowdown before such a frame is not forgotten. */
        long own_=(r[0x0e]==8) ? x16_of(r) : -1;
        /* the +40 chain starts only once the movie has reached speed 40 in this area: before that it is
         * accelerating (forced), and the line is the movie's own position. */
        int same_=(i_>0 && g_refarea[i_-1]==g_refarea[i_]);
        g_ref40[i_]=(uint8_t)(((same_ && g_ref40[i_-1]) || (r[0x0e]==8 && (int8_t)r[0x57]>=40)) ? 1 : 0);
        long car_=(same_ && g_ref40[i_-1] && g_refx[i_-1]>=0) ? g_refx[i_-1]+40 : -1;
        g_refx[i_]= own_>car_ ? own_ : car_; } }
    { uint8_t e_; if(!getenv("POLE_NOCAL") && pole_enemy(r,&e_)) ok_pole_enemy=1; }  /* POLE_NOCAL=1: positive control */
    ok_ges[r[0x0e]]=1; ok_oper[r[OPERMODE]]=1; ok_world[r[WORLDNUM]]=1;
    ok_area[r[AREAPTR]]=1; ok_pstate[r[PSTATE]&3]=1; ok_size[r[0x754]]=1;
    ok_wzc[r[0x6d6]]=1; ok_alt[r[0x752]]=1; ok_lock[r[0x723]]=1;
    /* Object-slot lens (L7).  Learn every id the reference line ever parks in a slot,
     * live or stale, so a stale byte cannot masquerade as novel; judge only LIVE slots. */
    for(int q=0;q<6;q++) ok_enid[r[ENID+q]]=1;
    { int n=0; for(int q=0;q<6;q++) if(r[ENID+q]==0x31) n++; if(n>ok_nstarflag) ok_nstarflag=n; }
}
/* Report each (class, VALUE) pair once, not each class once: otherwise the first mundane
 * WorldNumber masks the one that matters.  vals[] carries the offending value per class. */
static uint8_t anom_seen_val[NANOM][256];
static long g_px=-1, g_py=-1;   /* previous frame's position, for the discontinuity test */
static long g_px16=-1; static uint32_t g_parea=0; static int g_pges=0;   /* class 21: previous frame, 1/16 px */
static inline unsigned anom_mask(const uint8_t *r, uint8_t *vals){
    /* 19 classes; see ANOM_NAME */
    unsigned m=0;
    if(r[0x0e]==0) return 0;                       /* mid-load: the RAM is being reinitialised */
    if(r[0xb5]==0 && r[PY]>=0xfa){ m|=1u<<0; vals[0]=r[PY]; }  /* F210's 2-px doorway window */
    if(!ok_ges[r[0x0e]]){ m|=1u<<1; vals[1]=r[0x0e]; }
    if(!ok_oper[r[OPERMODE]]){ m|=1u<<2; vals[2]=r[OPERMODE]; }
    if(!ok_world[r[WORLDNUM]]){ m|=1u<<3; vals[3]=r[WORLDNUM]; }
    if(!ok_area[r[AREAPTR]]){ m|=1u<<4; vals[4]=r[AREAPTR]; }
    for(int q=0;q<6;q++) if(r[ENID+q]>0x36){ m|=1u<<5; vals[5]=r[ENID+q]; }  /* 6 slots: $16-$1b */
    if(r[0x6cb]){ m|=1u<<6; vals[6]=r[0x6cb]; }
    if(r[0x300]>80){ m|=1u<<7; vals[7]=r[0x300]; }
    if(!ok_pstate[r[PSTATE]&3]){ m|=1u<<8; vals[8]=r[PSTATE]&3; }
    if(!ok_size[r[0x754]]){ m|=1u<<9; vals[9]=r[0x754]; }
    if(!ok_wzc[r[0x6d6]]){ m|=1u<<10; vals[10]=r[0x6d6]; }     /* the 3,957-frame cell */
    if(!ok_alt[r[0x752]]){ m|=1u<<11; vals[11]=r[0x752]; }
    if(!ok_lock[r[0x723]]){ m|=1u<<12; vals[12]=r[0x723]; }
    if(r[0x6cd]){ m|=1u<<13; vals[13]=r[0x6cd]; }
    if(r[0x6cc]){ m|=1u<<14; vals[14]=r[0x6cc]; }
    if(r[0x6cf]){ m|=1u<<15; vals[15]=r[0x6cf]; }
    /* The object-slot lens (L7).  17: a LIVE slot (Enemy_Flag != 0) holding an id the reference
     * line never parked in any slot here -- the general "the parser put something impossible in a
     * slot" detector.  18: StarFlagObject ($31) in any slot at all, live or not -- that is F258's
     * 857-frame mechanism.  It is calibrated by COUNT, not by presence: the end-of-level castle
     * legitimately parks one, so the class fires only when MORE slots hold $31 than the reference
     * line ever holds here.  value = the count, bit 7 set when at least one of them is live
     * (Enemy_Flag != 0), i.e. when it would actually be dispatched by ProcELoop. */
    for(int q=0;q<6;q++) if(r[ENFLAG+q] && !ok_enid[r[ENID+q]]){ m|=1u<<17; vals[17]=r[ENID+q]; }
    { int n=0, live=0; for(int q=0;q<6;q++) if(r[ENID+q]==0x31){ n++; if(r[ENFLAG+q]) live++; }
      if(n>ok_nstarflag){ m|=1u<<18; vals[18]=(uint8_t)(n|(live?0x80:0)); } }
    if(!ok_pole_enemy){ uint8_t e_; if(pole_enemy(r,&e_)){ m|=1u<<19; vals[19]=e_; } }
    { long i_=g_curf-g_root_f;
      if(i_>=0 && i_<REFN && g_refx[i_]>=0 && r[0x0e]==8 && area_of(r)==g_refarea[i_]){
          long lead=x16_of(r)-g_refx[i_];
          if(lead>0){ m|=1u<<20; vals[20]=(uint8_t)(lead>255?255:lead);
              if(lead>g_maxlead){ g_maxlead=lead; g_maxlead_f=g_curf; }
              if(g_ref40[i_] && lead>g_maxlead40){ g_maxlead40=lead; g_maxlead40_f=g_curf; } } } }
    /* Mario cannot move more than ~4 px horizontally or ~8 px vertically in one frame of normal
     * play.  Anything larger is a clip, an ejection or a teleport -- the general glitch detector. */
    { long cx=(long)r[PPAGE]*256+r[PX], cy=(long)r[PYHI]*256+r[PY];
      if(g_px>=0 && (labs(cx-g_px)>5 || labs(cy-g_py)>9)){ m|=1u<<16;
          long d=labs(cx-g_px)>5?labs(cx-g_px):labs(cy-g_py); vals[16]=(uint8_t)(d>255?255:d); }
      g_px=cx; g_py=cy; }
    /* Class 21 (N10): Mario moved more than 40/16 px (2.5 px) forward in one frame, in control on both
     * frames, same area, and less than the 5 px that class 16 already reports.  The reference movie never
     * does it anywhere (max step exactly 2.5 px in all eight levels).  This is the literal ingredient
     * the near-misses lack: F316 needs 3.06 px in one frame, F324 3.2, F318/F334 2.75.  value = step. */
    { long x16=x16_of(r); uint32_t ar=area_of(r);
      if(g_px16>=0 && g_pges==8 && r[0x0e]==8 && ar==g_parea){ long dx=x16-g_px16;
          static long thr_=-1; if(thr_<0){ const char *e_=getenv("STEP_THR"); thr_=e_?atol(e_):40; }   /* STEP_THR=39: positive control */
          if(dx>thr_ && dx<=80){ m|=1u<<21; vals[21]=(uint8_t)dx; } }
      g_px16=x16; g_parea=ar; g_pges=r[0x0e]; }
    return m;
}
typedef struct { uint64_t key; int32_t frame; int32_t plen; int32_t sidx; int32_t visits; int32_t prog; } Cell;

int main(int argc, char **argv) {
    if (argc < 4) { fprintf(stderr,"usage: %s CORE.so ROM.nes INPUTS.bin --root N [opts]\n",argv[0]); return 2; }
    const char *core=argv[1], *rom=argv[2], *inputs=argv[3], *outdir="runs/E3";
    long root=-1, input_skip=2, ncells=150000, rlo=8, rhi=64, horizon=900, secs=300, report=15, coast=400;
    long xcell=4, ycell=8, scell=64, spdcell=8, ecell=16, seedwr=1, probex=-1, nullmax=200, relcell=2;
    long subcell=0, ysubcell=0, frccell=0, yfrccell=0;
    int gesdeath=1;   /* F300: a rollout is dead as soon as GES = 11 (PlayerDeath) / 6 (PlayerLoseLife) or $b5 > 1 (below the screen) */
    long kaddr[4]; long kdiv[4]; int nkey=0;   /* --keyaddr ADDR[/DIV]: raw RAM bytes in the cell key */
    long wlo=-1, whi=-1, maxaddr=-1, maxw=0, anomaly=0;
    double tournp=0.75;
    long gaddr[8], gval[8]; int ngoal=0; long baseline=-1; const char *seedpaths[8]; int nseed=0;
    long raddr[8], rval[8]; int nreq=0; long progx=-1, progoff=0, progfw=5;
    for (int i=4;i<argc;i++){
        if(!strcmp(argv[i],"--root")) root=strtol(argv[++i],NULL,0);
        else if(!strcmp(argv[i],"--input-skip")) input_skip=strtol(argv[++i],NULL,0);
        else if(!strcmp(argv[i],"--cells")) ncells=strtol(argv[++i],NULL,0);
        else if(!strcmp(argv[i],"--horizon")) horizon=strtol(argv[++i],NULL,0);
        else if(!strcmp(argv[i],"--coast")) coast=strtol(argv[++i],NULL,0);
        else if(!strcmp(argv[i],"--seed")) rngs=strtoull(argv[++i],NULL,0)*2654435761ULL+88172645463325252ULL;
        else if(!strcmp(argv[i],"--secs")) secs=strtol(argv[++i],NULL,0);
        else if(!strcmp(argv[i],"--report")) report=strtol(argv[++i],NULL,0);
        else if(!strcmp(argv[i],"--out")) outdir=argv[++i];
        else if(!strcmp(argv[i],"--xcell")) xcell=strtol(argv[++i],NULL,0);
        else if(!strcmp(argv[i],"--ycell")) ycell=strtol(argv[++i],NULL,0);
        else if(!strcmp(argv[i],"--scell")) scell=strtol(argv[++i],NULL,0);
        else if(!strcmp(argv[i],"--relcell")) relcell=strtol(argv[++i],NULL,0);
        else if(!strcmp(argv[i],"--subcell")) subcell=strtol(argv[++i],NULL,0);
        else if(!strcmp(argv[i],"--ysubcell")) ysubcell=strtol(argv[++i],NULL,0);
        else if(!strcmp(argv[i],"--frccell")) frccell=strtol(argv[++i],NULL,0);
        else if(!strcmp(argv[i],"--no-ges-death")) gesdeath=0;
        else if(!strcmp(argv[i],"--keyaddr") && nkey<4) { char *e; kaddr[nkey]=strtol(argv[++i],&e,0); kdiv[nkey]=(*e=='/')?strtol(e+1,NULL,0):1; if(kdiv[nkey]<1) kdiv[nkey]=1; nkey++; }
        else if(!strcmp(argv[i],"--yfrccell")) yfrccell=strtol(argv[++i],NULL,0);
        else if(!strcmp(argv[i],"--max-addr")) maxaddr=strtol(argv[++i],NULL,0);
        else if(!strcmp(argv[i],"--max-weight")) maxw=strtol(argv[++i],NULL,0);
        else if(!strcmp(argv[i],"--anomaly")) anomaly=1;
        else if(!strcmp(argv[i],"--watch-x")){ char*t=argv[++i]; wlo=strtol(t,NULL,0);
            char*c2=strchr(t,','); if(c2) whi=strtol(c2+1,NULL,0); else whi=wlo; }
        else if(!strcmp(argv[i],"--spdcell")) spdcell=strtol(argv[++i],NULL,0);
        else if(!strcmp(argv[i],"--enemycell")) ecell=strtol(argv[++i],NULL,0);
        else if(!strcmp(argv[i],"--no-seed-wr")) seedwr=0;
        else if(!strcmp(argv[i],"--probe-x")) probex=strtol(argv[++i],NULL,0);
        else if(!strcmp(argv[i],"--null-max")) nullmax=strtol(argv[++i],NULL,0);
        else if(!strcmp(argv[i],"--tournp")) tournp=strtod(argv[++i],NULL);
        else if(!strcmp(argv[i],"--baseline")) baseline=strtol(argv[++i],NULL,0);
        else if(!strcmp(argv[i],"--prog-x")) progx=strtol(argv[++i],NULL,0);
        else if(!strcmp(argv[i],"--prog-off")) progoff=strtol(argv[++i],NULL,0);
        else if(!strcmp(argv[i],"--prog-fw")) progfw=strtol(argv[++i],NULL,0);
        else if(!strcmp(argv[i],"--require-ram")){
            char *sp=strdup(argv[++i]), *tok=strtok(sp,",");
            while(tok && nreq<8){ char *eq=strchr(tok,'='); if(eq){ *eq=0;
                raddr[nreq]=strtol(tok,NULL,0); rval[nreq]=strtol(eq+1,NULL,0); nreq++; }
                tok=strtok(NULL,","); } }
        else if(!strcmp(argv[i],"--seed-path")){ if(nseed<8) seedpaths[nseed++]=argv[++i]; else i++; }
        else if(!strcmp(argv[i],"--goal-ram")){
            char *sp=strdup(argv[++i]), *tok=strtok(sp,",");
            while(tok && ngoal<8){ char *eq=strchr(tok,'='); if(eq){ *eq=0;
                gaddr[ngoal]=strtol(tok,NULL,0); gval[ngoal]=strtol(eq+1,NULL,0); ngoal++; }
                tok=strtok(NULL,","); } }
        else if(!strcmp(argv[i],"--rollout")){ char*s=argv[++i]; rlo=strtol(s,NULL,0); char*c=strchr(s,','); if(c) rhi=strtol(c+1,NULL,0); }
        else { fprintf(stderr,"unknown option %s\n",argv[i]); return 2; }
    }
    if (root < 0) { fprintf(stderr,"--root is required\n"); return 2; }

    void *h = dlopen(core, RTLD_NOW|RTLD_LOCAL);
    if(!h){ fprintf(stderr,"dlopen: %s\n",dlerror()); return 1; }
    retro_set_environment_t g_retro_set_environment; retro_set_video_refresh_t g_retro_set_video_refresh;
    retro_set_audio_sample_t g_retro_set_audio_sample; retro_set_audio_sample_batch_t g_retro_set_audio_sample_batch;
    retro_set_input_poll_t g_retro_set_input_poll; retro_set_input_state_t g_retro_set_input_state;
    retro_init_t g_retro_init; retro_deinit_t g_retro_deinit; retro_load_game_t g_retro_load_game;
    retro_unload_game_t g_retro_unload_game; retro_get_memory_size_t g_retro_get_memory_size;
    SYM(retro_set_environment) SYM(retro_set_video_refresh) SYM(retro_set_audio_sample)
    SYM(retro_set_audio_sample_batch) SYM(retro_set_input_poll) SYM(retro_set_input_state)
    SYM(retro_init) SYM(retro_deinit) SYM(retro_load_game) SYM(retro_unload_game) SYM(retro_run)
    SYM(retro_serialize_size) SYM(retro_serialize) SYM(retro_unserialize)
    SYM(retro_get_memory_data) SYM(retro_get_memory_size)
    g_retro_set_environment(env_cb); g_retro_set_video_refresh(video_cb);
    g_retro_set_audio_sample(audio_cb); g_retro_set_audio_sample_batch(audio_batch_cb);
    g_retro_set_input_poll(input_poll_cb); g_retro_set_input_state(input_state_cb);
    g_retro_init();

    FILE *rf=fopen(rom,"rb"); if(!rf){ perror(rom); return 1; }
    fseek(rf,0,SEEK_END); long rsz=ftell(rf); fseek(rf,0,SEEK_SET);
    void *rdata=malloc(rsz); if(fread(rdata,1,rsz,rf)!=(size_t)rsz){ perror("rom"); return 1; } fclose(rf);
    struct retro_game_info gi={rom,rdata,(size_t)rsz,NULL};
    if(!g_retro_load_game(&gi)){ fprintf(stderr,"load_game failed\n"); return 1; }

    FILE *inf=fopen(inputs,"rb"); if(!inf){ perror(inputs); return 1; }
    fseek(inf,0,SEEK_END); long nin=ftell(inf); fseek(inf,0,SEEK_SET);
    uint8_t *in=malloc(nin); if(fread(in,1,nin,inf)!=(size_t)nin){ perror("inputs"); return 1; } fclose(inf);

    for(int i=0;i<ngoal;i++){ g_gaddr[i]=gaddr[i]; g_gval[i]=gval[i]; } g_ngoal=ngoal;
    for(int i=0;i<nreq;i++){ g_raddr[i]=raddr[i]; g_rval[i]=rval[i]; } g_nreq=nreq;
    g_ssz = g_retro_serialize_size();
    uint8_t *ram = RAMP();
    for(long i=0;i<root;i++){ cur_pad=in[i+input_skip]; g_retro_run(); }
    ram = RAMP();
    g_root_state = malloc(g_ssz); g_retro_serialize(g_root_state, g_ssz);
    g_lives0 = ram[LIVES];
    long wr_last=-1; for(long i=0;i<root;i++) if(in[i+input_skip]) wr_last=i;

    printf("root=%ld  state=%zu B  lives=%u  area=$%02x  x=%d  y=%d  WR last input before root=%ld\n",
           root,g_ssz,ram[LIVES],ram[AREAPTR],ram[PPAGE]*256+ram[PX],ram[PYHI]*256+ram[PY],wr_last);

    size_t cap=1; while((long)cap < ncells*2) cap<<=1;
    Cell *tab=calloc(cap,sizeof(Cell));
    int32_t *live=malloc(sizeof(int32_t)*ncells); long nlive=0;
    uint8_t *arena=malloc((size_t)ncells*g_ssz);
    long pslot=horizon+8;
    uint8_t *parena=malloc((size_t)ncells*pslot);
    if(!tab||!live||!arena||!parena){ fprintf(stderr,"archive alloc failed\n"); return 1; }
    printf("archive: %ld cells, state %.2f GB, paths %.2f GB\n",
           ncells,(double)ncells*g_ssz/1e9,(double)ncells*pslot/1e9);
    uint8_t *path=malloc(pslot);
    uint8_t *probebuf=malloc(g_ssz);

    #define KEYOF(r) ({ long ax=(r)[PPAGE]*256+(r)[PX]; long ay=(r)[PYHI]*256+(r)[PY]; \
        long sl=(r)[SLPAGE]*256+(r)[SLX]; int8_t sp=(int8_t)(r)[PXSPD]; \
        long rl=ax-sl; if(rl<0) rl=0; if(rl>255) rl=255; \
        uint64_t ed=0; if(ecell) for(int q=0;q<5;q++) if((r)[ENID+q]) \
            ed = ed*1000003ULL + (uint64_t)((r)[ENID+q])*131ULL + (uint64_t)((r)[ENX+q]/ecell); \
        uint64_t mv = maxaddr>=0 ? (uint64_t)(r)[maxaddr] : 0; \
        uint64_t k = (uint64_t)(ax/xcell) | ((uint64_t)(ay/ycell)<<14) | ((uint64_t)((sp+128)/spdcell)<<26) \
                   | ((uint64_t)((r)[PSTATE]&3)<<32) | ((uint64_t)(rl/relcell)<<34) | ((uint64_t)((r)[SCTIMER]!=0)<<42) \
                   | ((uint64_t)(sl/scell)<<43) | ((uint64_t)(r)[AREAPTR]<<48) \
                   | ((uint64_t)((r)[GES]&15)<<56); \
        k ^= ed*0x9e3779b97f4a7c15ULL; k ^= mv*0x94d049bb133111ebULL; \
        if(subcell)  k ^= (uint64_t)((r)[PXSUB]/subcell)*0xd6e8feb86659fd93ULL; \
        if(ysubcell) k ^= (uint64_t)((r)[PYSUB]/ysubcell)*0xa0761d6478bd642fULL; \
        if(frccell)  k ^= (uint64_t)((r)[PXFRAC]/frccell)*0x8ebc6af09c88c6e3ULL; \
        if(yfrccell) k ^= (uint64_t)((r)[PYFRAC]/yfrccell)*0x589965cc75374cc3ULL; \
        for(int kq=0;kq<nkey;kq++) k ^= (uint64_t)((r)[kaddr[kq]]/kdiv[kq]+1)*(0x2545f4914f6cdd1dULL+0x9e3779b97f4a7c15ULL*(uint64_t)kq); k ^= k>>29; k *= 0xbf58476d1ce4e5b9ULL; k ^= k>>32; k|1ULL; })

    long inserted=0, improved=0, rollouts=0, frames=0, goals=0, evict=0, deaths=0, probes=0;
    unsigned anom_seen=0; long anom_hits=0;
    /* promise: how far ahead of a constant-max-speed schedule this cell is (2.5 px/frame),
     * minus a visit penalty so exploration spreads instead of collapsing onto one cell. */
    #define PROMISE(c) ((long)tab[c].prog*2 - ((long)tab[c].frame-root)*progfw - (long)tab[c].visits*3)
    long best_last=1L<<30, best_prog=0, best_frame=1L<<30, best_off=0, best_off_near=0, best_watch=0, best_max=-1;
    long wcurve[256], wcurve0[256];   /* earliest frame reaching each rel in the window; ...0 = with Player_X_Scroll==0 */
    for(int i=0;i<256;i++){ wcurve[i]=1L<<30; wcurve0[i]=1L<<30; }

    #define INSERT(F,PL) do { \
        uint64_t k_=KEYOF(ram); size_t p_=k_&(cap-1); \
        while(tab[p_].key && tab[p_].key!=k_) p_=(p_+1)&(cap-1); \
        long ax_=(long)ram[PPAGE]*256+ram[PX]; if(ax_>best_prog) best_prog=ax_; \
        long off_=ax_-((long)ram[SLPAGE]*256+ram[SLX]); \
        if(ram[GES]==8 && off_>=0 && off_<=255){ if(off_>best_off) best_off=off_; \
            if(progx>=0 && ax_>=progx-96 && off_>best_off_near) best_off_near=off_; \
            if(wlo>=0 && ax_>=wlo && ax_<=whi){ \
                if((long)(F)<wcurve[off_]) wcurve[off_]=(long)(F); \
                if(ram[0x6ff]==0 && (long)(F)<wcurve0[off_]){ wcurve0[off_]=(long)(F); \
                    if(off_>=132){ char fn3[512]; snprintf(fn3,sizeof fn3,"%s/warpable_rel%ld_f%ld.path",outdir,off_,(long)(F)); \
                        FILE *o3=fopen(fn3,"wb"); \
                        if(o3){ fprintf(o3,"root %ld len %ld x %ld rel %ld frame %ld xscroll 0\n",root,(long)(PL),ax_,off_,(long)(F)); \
                                fwrite(path,1,(size_t)(PL),o3); fclose(o3); } \
                        printf("  *** WARP-CAPABLE: x=%ld rel=%ld frame=%ld Player_X_Scroll=0 (WR entry 7169) ***\n", \
                               ax_,off_,(long)(F)); fflush(stdout); } } } \
            if(wlo>=0 && ax_>=wlo && ax_<=whi && off_>best_watch){ best_watch=off_; \
                char fn2[512]; snprintf(fn2,sizeof fn2,"%s/watch_rel%ld.path",outdir,off_); \
                FILE *o2=fopen(fn2,"wb"); \
                if(o2){ fprintf(o2,"root %ld len %ld x %ld rel %ld frame %ld xscroll %u\n", \
                        root,(long)(PL),ax_,off_,(long)(F),ram[0x6ff]); \
                        fwrite(path,1,(size_t)(PL),o2); fclose(o2); } \
                printf("  WATCH x=%ld rel=%ld frame=%ld Player_X_Scroll=%u %s\n",ax_,off_,(long)(F), \
                       ram[0x6ff], off_>=132?"  <-- WARP-CAPABLE LEAD":""); fflush(stdout); } } \
        int32_t pg_=(int32_t)((progx>=0 ? -labs(ax_-progx) : ax_) + progoff*off_ \
                              + (maxaddr>=0 ? maxw*(long)ram[maxaddr] : 0)); \
        if(maxaddr>=0 && (long)ram[maxaddr]>best_max){ best_max=(long)ram[maxaddr]; \
            char fnm[512]; snprintf(fnm,sizeof fnm,"%s/max_%02lx_%ld.path",outdir,maxaddr,best_max); \
            FILE *om=fopen(fnm,"wb"); \
            if(om){ fprintf(om,"root %ld len %ld addr 0x%lx value %ld frame %ld x %ld\n", \
                            root,(long)(PL),maxaddr,best_max,(long)(F),ax_); \
                    fwrite(path,1,(size_t)(PL),om); fclose(om); } \
            printf("  MAX $%04lx = %ld  at frame %ld x %ld%s\n",maxaddr,best_max,(long)(F),ax_, \
                   best_max>=227?"   *** REACHES Block_BBuf_Low ***":(best_max>67?"   (above the WR's 67)":"")); \
            fflush(stdout); } \
        g_curf=(long)(F); \
        if(anomaly && g_calibrating){ anom_learn(ram); } \
        else if(anomaly){ uint8_t av_[NANOM]={0}; unsigned am_=anom_mask(ram,av_); \
            if(am_){ unsigned nw_=0; \
                for(int b_=0;b_<NANOM;b_++) if((am_>>b_&1) && !anom_seen_val[b_][av_[b_]]){ \
                    anom_seen_val[b_][av_[b_]]=1; nw_|=1u<<b_; } \
                anom_seen|=nw_; if(nw_) anom_hits++; \
                for(int b_=0;b_<NANOM;b_++) if(nw_>>b_&1){ \
                    char fa[512]; snprintf(fa,sizeof fa,"%s/anom_%d_f%ld.path",outdir,b_,(long)(F)); \
                    FILE *oa=fopen(fa,"wb"); \
                    if(oa){ fprintf(oa,"root %ld len %ld anomaly %d %s value %u frame %ld x %ld y %ld\n", \
                            root,(long)(PL),b_,ANOM_NAME[b_],av_[b_],(long)(F), \
                            (long)ram[PPAGE]*256+ram[PX],(long)ram[PYHI]*256+ram[PY]); \
                            fwrite(path,1,(size_t)(PL),oa); fclose(oa); } \
                    printf("  *** ANOMALY %s = %u  frame %ld x %ld y %ld  %s%s\n",ANOM_NAME[b_],av_[b_], \
                           (long)(F),(long)ram[PPAGE]*256+ram[PX],(long)ram[PYHI]*256+ram[PY],fa, \
                           (b_==3 && av_[b_]==7) ? "   *** WORLD 8 REACHED ***" : \
                           (b_==3 && av_[b_]==35) ? "   (the Minus World -- H6, refuted)" : \
                           (b_==10) ? "   *** WARP ZONE CONTROL SET -- THE 3957-FRAME CELL ***" : \
                           (b_==5||b_==6) ? "   *** OOB ENEMY PRIMITIVE ***" : \
                           (b_==18) ? "   *** SECOND STAR FLAG -- F258'S 857 FRAMES ***" : \
                           (b_==19) ? "   *** ENEMY AT THE FLAGPOLE (H57: bounce into a glitch grab) ***" : \
                           (b_==17) ? "   *** OBJECT-SLOT ANOMALY (F258 class) ***" : ""); } \
                fflush(stdout); } } \
        if(!req_ok(ram)) break; \
        if(!tab[p_].key){ \
            if(nlive>=ncells) evict++; \
            else { g_retro_serialize(arena+(size_t)nlive*g_ssz,g_ssz); \
                   memcpy(parena+(size_t)nlive*pslot,path,(size_t)(PL)); \
                   tab[p_]=(Cell){k_,(int32_t)(F),(int32_t)(PL),(int32_t)nlive,0,pg_}; \
                   live[nlive]=(int32_t)p_; nlive++; inserted++; } \
        } else if((long)(F) < tab[p_].frame){ \
            g_retro_serialize(arena+(size_t)tab[p_].sidx*g_ssz,g_ssz); \
            memcpy(parena+(size_t)tab[p_].sidx*pslot,path,(size_t)(PL)); \
            tab[p_].frame=(int32_t)(F); tab[p_].plen=(int32_t)(PL); tab[p_].prog=pg_; improved++; \
        } } while(0)

    #define ONGOAL(F,PL) do { \
        goals++; \
        if(g_ngoal){ if((long)(F)<best_frame){ best_frame=(long)(F); \
              char fn[512]; snprintf(fn,sizeof fn,"%s/goal_%ld.path",outdir,(long)(F)); \
              FILE *o=fopen(fn,"wb"); \
              if(o){ fprintf(o,"root %ld len %ld goal_frame %ld baseline %ld\n",root,(long)(PL),(long)(F),baseline); \
                     fwrite(path,1,(size_t)(PL),o); fclose(o); } \
              printf("  GOAL frame=%ld  (baseline %ld, %+ld)%s\n",(long)(F),baseline,(long)(F)-baseline, \
                     (baseline>0&&(long)(F)<baseline)?"   *** AHEAD OF THE WR ***":""); fflush(stdout); } break; } \
        long cut=0; long li=trim_path(path,(PL),root,coast,wr_last,&cut,best_last==(1L<<30)?0:best_last); \
        if(li<best_last){ best_last=li; \
            char fn[512]; snprintf(fn,sizeof fn,"%s/best_%ld.path",outdir,li); \
            FILE *o=fopen(fn,"wb"); \
            if(o){ fprintf(o,"root %ld len %ld cut %ld victory %ld last_input %ld\n",root,(PL),cut,(long)(F),li); \
                   fwrite(path,1,(size_t)(PL),o); fclose(o); } \
            printf("  GOAL victory=%ld  last_input=%ld  (WR 17846) %s\n",(long)(F),li, \
                   li<17846?"  *** RECORD ***":""); fflush(stdout); } \
        } while(0)

    /* root cell */
    { long plen=0; ram=RAMP(); INSERT(root,plen); }
    if(!seedwr) g_calibrating=0;

    /* seed the archive with the movie's own continuation: the finder starts from an incumbent
     * and improves it, instead of having to discover the axe by chance. */
    if(seedwr){
        g_retro_unserialize(g_root_state,g_ssz); ram=RAMP();
        g_root_f=root; g_curf=root; for(long q=0;q<REFN;q++) g_refx[q]=-1;
        anom_learn(ram);
        long plen=0, f=root;
        for(long i=0;i<horizon && root+i+input_skip < nin; i++){
            cur_pad=in[root+i+input_skip]; g_retro_run(); f++; path[plen++]=cur_pad; ram=RAMP();
            if(ram[LIVES]<g_lives0||ram[OPERMODE]==3) break;
            if(goal_hit(ram)){ ONGOAL(f,plen); break; }
            INSERT(f,plen);
        }
        g_calibrating=0;
        { for(int b=0;b<NANOM;b++) for(int q=0;q<256;q++) anom_seen_val[b][q]=0; }
    if(anomaly){ int ng=0,no=0,nw=0,na=0,np=0,ne=0;
            for(int q=0;q<256;q++){ ng+=ok_ges[q]; no+=ok_oper[q]; nw+=ok_world[q]; na+=ok_area[q]; np+=ok_pstate[q]; ne+=ok_enid[q]; }
            printf("anomaly calibration from the WR line: %d GES / %d OperMode / %d World / %d AreaPointer / %d PlayerState / %d Enemy_ID values are normal here\n",ng,no,nw,na,np,ne); }
        printf("seeded WR line: %ld cells, incumbent last_input=%ld\n",nlive,best_last);
        fflush(stdout);
    }
    for(int si=0; si<nseed; si++){
        FILE *sf=fopen(seedpaths[si],"rb");
        if(!sf){ perror(seedpaths[si]); continue; }
        fseek(sf,0,SEEK_END); long sn=ftell(sf); fseek(sf,0,SEEK_SET);
        uint8_t *sb=malloc(sn); if(fread(sb,1,sn,sf)!=(size_t)sn){ perror("seed"); return 1; } fclose(sf);
        if(sn>0) sb[sn-1]|=0x20;                    /* a vertical pipe entry needs Down (F74) */
        g_retro_unserialize(g_root_state,g_ssz); ram=RAMP();
        long plen=0, f=root, before=nlive;
        for(long i=0;i<sn && i<horizon;i++){
            cur_pad=sb[i]; g_retro_run(); f++; path[plen++]=cur_pad; ram=RAMP();
            if(ram[LIVES]<g_lives0||ram[OPERMODE]==3){ printf("  seed %s DIED at +%ld\n",seedpaths[si],i); break; }
            if(goal_hit(ram)){ ONGOAL(f,plen); break; }
            INSERT(f,plen);
        }
        /* keep going with blank input so the pipe animation completes and the goal can fire */
        for(long i=0;i<200 && f<root+horizon;i++){
            cur_pad=0; g_retro_run(); f++; path[plen++]=0; ram=RAMP();
            if(ram[LIVES]<g_lives0||ram[OPERMODE]==3) break;
            if(goal_hit(ram)){ ONGOAL(f,plen); break; }
            INSERT(f,plen);
        }
        printf("  seeded %s: %ld frames, +%ld cells\n",seedpaths[si],sn,nlive-before); fflush(stdout);
        free(sb);
    }

    double t0=now(), tnext=t0+report, tend=t0+secs;
    while(now()<tend){
        long pick=live[rndn((uint32_t)nlive)];
        if(nlive>2 && (rnd()%1000) < (uint64_t)(tournp*1000))
            for(int t=0;t<7;t++){ long c=live[rndn((uint32_t)nlive)];
                if(PROMISE(c)>PROMISE(pick)) pick=c; }
        Cell *cl=&tab[pick]; cl->visits++;
        if(!g_retro_unserialize(arena+(size_t)cl->sidx*g_ssz,g_ssz)){ fprintf(stderr,"unserialize failed\n"); return 1; }
        ram=RAMP();
        long plen=cl->plen; memcpy(path,parena+(size_t)cl->sidx*pslot,(size_t)plen);
        g_px=-1; g_py=-1; g_px16=-1;
        long f=cl->frame;

        long L=rlo+(rhi>rlo?(long)rndn((uint32_t)(rhi-rlo+1)):0);
        if(f+L>root+horizon) L=root+horizon-f;
        rollouts++;
        static const uint8_t ACT[] = { 0x82,0x82,0x82,0x82,0x83,0x83,0x83,0x80,0x81,0x00,0x01,
                                       0x42,0x43,0x40,0xC2,0xC3,0x02,0x03,0xA2,0x22 };
        static const int DUR[] = {1,1,1,2,2,3,3,4,4,5,6,8,10,12,16,20,28};
        while(L>0){
            uint8_t a=ACT[rndn((uint32_t)(sizeof ACT))]; long d=DUR[rndn((uint32_t)(sizeof DUR/sizeof DUR[0]))];
            if(d>L) d=L;
            long j;
            for(j=0;j<d;j++){
                cur_pad=a; g_retro_run(); frames++; f++; path[plen++]=a; ram=RAMP();
                if(ram[LIVES]<g_lives0||ram[OPERMODE]==3){ deaths++; L=0; break; }
                if(gesdeath && (ram[GES]==11||ram[GES]==6||ram[PYHI]>1)){ deaths++; L=0; break; }
                if(goal_hit(ram)){ ONGOAL(f,plen); L=0; break; }
                INSERT(f,plen);
                /* THE OBJECTIVE, measured directly: if we stopped pressing buttons right here,
                 * would Mario still reach the axe?  The movie ends at its last input (F17), so a
                 * "yes" whose last input beats the incumbent IS the record.  Cheap because the
                 * probe quits the moment Mario is stopped on the ground. */
                if(probex>=0 && (long)(ram[PPAGE]*256+ram[PX])>=probex){
                    long li_=wr_last; for(long q_=0;q_<plen;q_++) if(path[q_]) li_=root+q_;
                    if(li_<best_last){
                        probes++;
                        g_retro_serialize(probebuf,g_ssz);
                        long win=-1;
                        for(long t_=0;t_<nullmax;t_++){
                            cur_pad=0; g_retro_run(); frames++; ram=RAMP();
                            if(ram[LIVES]<g_lives0||ram[OPERMODE]==3) break;
                            if(goal_hit(ram)){ win=f+t_+1; break; }
                            if(ram[PXSPD]==0 && ram[PSTATE]==0) break;   /* stopped: never moves again */
                        }
                        g_retro_unserialize(probebuf,g_ssz); ram=RAMP();
                        if(win>=0){
                            best_last=li_; goals++;
                            char fn[512]; snprintf(fn,sizeof fn,"%s/best_%ld.path",outdir,li_);
                            FILE *o=fopen(fn,"wb");
                            if(o){ fprintf(o,"root %ld len %ld cut %ld victory %ld last_input %ld\n",
                                           root,plen,plen,win,li_); fwrite(path,1,(size_t)plen,o); fclose(o); }
                            printf("  COAST GOAL victory=%ld last_input=%ld (WR 17846)%s\n",
                                   win,li_,li_<17846?"   *** RECORD ***":""); fflush(stdout);
                        }
                    }
                }
            }
            if(j<d) break;
            L-=d;
        }

        if(now()>=tnext){
            double el=now()-t0; char bl[32]; long bb = g_ngoal?best_frame:best_last;
            if(bb==(1L<<30)) snprintf(bl,sizeof bl,"-"); else snprintf(bl,sizeof bl,"%ld",bb);
            printf("[%6.0fs] cells=%ld rollouts=%ld frames=%.2fM (%.0fk fps) goals=%ld deaths=%ld "
                   "best=%s maxx=%ld maxrel=%ld maxaddr=%ld anom=0x%05x improved=%ld evict=%ld\n",
                   el,nlive,rollouts,frames/1e6,frames/el/1e3,goals,deaths,bl,best_prog,best_off,best_max,anom_seen,improved,evict);
            if(wlo>=0){ printf("          mint curve (rel: earliest frame | x-scroll 0):");
                for(int q=112;q<=160;q+=2) if(wcurve[q]<(1L<<30))
                    printf(" %d:%ld%s",q,wcurve[q],wcurve0[q]<(1L<<30)?"*":"");
                printf("\n"); }
            fflush(stdout); tnext=now()+report;
        }
    }
    char bl[32]; long bb2 = g_ngoal?best_frame:best_last;
    if(bb2==(1L<<30)) snprintf(bl,sizeof bl,"-"); else snprintf(bl,sizeof bl,"%ld",bb2);
    printf("done: cells=%ld rollouts=%ld frames=%.2fM goals=%ld deaths=%ld best_last_input=%s (WR 17846) maxx=%ld\n",
           nlive,rollouts,frames/1e6,goals,deaths,bl,best_prog);
    printf("max lead over the cap line: %ld/16 px at frame %ld; after the reference reached top speed: %ld/16 px at frame %ld\n",g_maxlead,g_maxlead_f,g_maxlead40,g_maxlead40_f);
    g_retro_unload_game(); g_retro_deinit(); dlclose(h);
    return 0;
}
