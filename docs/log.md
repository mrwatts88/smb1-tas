# Session log (append-only; newest at the bottom)

## 2026-08-21 — Session 1: planning
**Did.** Researched the current state of the record (TASVideos publications, submission #8991S,
SMB1 Game Resources page, forum pp.59/62/63, user files, Wikipedia). Agreed target and
decisions with Matt (D1–D6). Wrote CLAUDE.md, PLAN.md, PROCESS.md, STATUS.md, docs/facts.md,
docs/hypotheses.md (H1–H20), docs/decisions.md, .gitignore, directory skeleton.

**Learned.** The warps record (#1715M, 17,868 frames) is from Jan 2011 and has survived
subpixel-perfect rewrites (2019) and two 2025 rewrites. Humans are 9 frames from the
RTA-rules TAS. ACE exists on NES only via cartridge swap; on FDS via the Minus World. No
public full-state exhaustive search exists (to verify in P0.8). Community bots were narrow.

Matt fixed the end-of-unit order: document → update STATUS → commit (last). Git initialized
and the scaffold committed. Then: pushed to a private GitHub repo; the Linux box becomes the
primary host (Matt will run sessions there); `docs/rom.md` added.

**Next.** P0.1 (tooling), P0.2 (fetch the .fm2, verify 17,868 frames + ROM hash), P0.5/P0.6
(disassembly models) can all proceed without the ROM. P0.3+ need the ROM in `roms/`.

## 2026-08-21 — Session 1 (cont.): P0.2 done on the Mac
**Did.** Matt supplied a dump (`Super Mario Bros. (World).nes`, NES 2.0 header). Downloaded the
#1715M movie (`data/wr/happylee-supermariobros,warped.fm2`), wrote `tools/verify_rom.py` and
`tools/fm2_info.py`. ROM data is byte-identical to TASVideos' (W) [!] (classic-header MD5/SHA1
match; movie romChecksum matches). Wrote a classic-header copy to `roms/` (gitignored).

**Learned.** Movie = 17,868 frames; last input is an A press on frame 17848 (0-based) followed
by 19 input-free frames (H1 baseline); Start first pressed on frame 41; L+R on 85 frames,
U+D never. The published length counts the trailing coast (F17).

**Next.** On the Linux box: copy the ROM into `roms/`, then P0.1 (tooling), P0.3 (sync the
WR and record the axe frame), P0.4 (RAM dump + slack table). P0.5/P0.6 need only the
disassembly.

## 2026-08-21 — Session 2 (Linux box): P0.1 tooling done
**Did.** First session on the Linux box (Fedora 43, i5-1335U, 15 GiB). ROM and WR movie were
already in place (ROM re-verified with `tools/verify_rom.py`). Host `sudo` needs a password, so
instead of blocking on Matt I built a rootless `toolbox` container (`smb1`) with FCEUX 2.6.6
(RPM Fusion, Lua 5.1), Xvfb, mono 6.12 (+libgdiplus) and dev tools; Mesen 2.1.1 runs natively;
BizHawk 2.11.1 runs on mono in the container. All three pass a headless Lua smoke test
(300 frames, RAM reads to a file). Wrote `tools/toolbox_setup.sh` (idempotent reproduce),
`tools/{fceux,mesen2,bizhawk}_run.sh`, `tools/lua/{smoke,bench}_*.lua`,
`docs/experiments/P0.1-tooling.md`; facts F18–F22.

**Learned.** Eight tooling gotchas (all in the experiment file): Mesen2 needs a pre-seeded
settings.json (else it opens the GUI wizard before checking `--testrunner`),
`DOTNET_SYSTEM_GLOBALIZATION_INVARIANT=1` on Fedora 43, and file output (emu.log isn't on
stdout); FCEUX defaults to real-time speed and segfaults in `emu.exit()` after finishing;
BizHawk hangs on invisible modal dialogs (sound device, config version) until config.ini is
seeded; `toolbox run` drops the caller's env. Throughput: FCEUX ≈1,400 fps, Mesen2 ≈400 fps,
BizHawk ≈100 fps under Lua loops — reference emulators only. Boot-time frame alignment differs
by emulator (F22) — P0.3 must pin it down.

**Next.** P0.3: replay the WR .fm2 in FCEUX (`--playmov` + Lua), confirm the ending, record
the axe frame; then the same via BizHawk (fm2→bk2 conversion) as the second emulator.

## 2026-08-21 — Session 2 (cont.): P0.3 done — the WR syncs in FCEUX and BizHawk
**Did.** Replayed #1715M in FCEUX with a Lua per-frame dump (full 2 KiB RAM + 23 key addresses +
joypad byte) and in BizHawk/NesHawk (after writing `tools/fm2_to_bk2.py`, because BizHawk's
on-the-fly fm2 import pops an invisible dialog). Wrote `tools/check_sync.py` (alignment from
joypad bytes, transitions, lag rows) and `tools/compare_dumps.py` (cross-emulator diff).
Fetched doppelganger's disassembly to `data/disasm/smbdis.asm`.

**Learned.** Both emulators sync; their game state is identical frame-for-frame (F23). The axe is
touched on fm2 frame 17867 (0-based) — the movie's last frame (F24). 24 lag frames before the axe,
one per area/pipe load (F24). Index conventions: FCEUX row i ↔ fm2 frame i−1, BizHawk row i ↔ fm2
frame i (F25). Level-entry frames recorded (F26). BizHawk pauses at movie end by default
(`Movies.MovieEndAction`), which freezes Lua frame loops — fixed in config.

**Next.** P0.4: slack table from `data/wr/fceux_wr.ram` (framerule phase at each flagpole/axe,
frames lost to rounding per level, RNG at each entry). Then P0.5 (timing model from the
disassembly, checked against the dump).

## 2026-08-21 — Session 2 (cont.): P0.4 done — slack table
**Did.** Derived the framerule mechanism from the disassembly (`DecTimers`, `RunStarFlagObj`,
`DelayToAreaEnd`, `ScreenRoutines`/`ScreenTimer`, `VerticalPipeEntry`/`ChangeAreaTimer`) and
verified it frame-exactly against the P0.3 RAM dump with `tools/slack_table.py`
(`docs/experiments/P0.4-slack-table.md`). Facts F27–F30, hypotheses H21–H24, H2 parked, H4 confirmed.

**Learned.** Flag levels: slack = post-frame ITC at the frame the star-flag interval timer is set
(v), deficit = 21 − v; countdown = 1 frame per timer unit. Main-level loads start control at
load + 154 + w (w = ITC when ScreenTimer is written at load+8) → pipe levels are quantized at
the *next* load; sub-area loads (bonus rooms, 4-2 wrong warp, 8-4 rooms) are not quantized.
**1-1 is 1 frame from the next framerule**; then 1-2 (8), 4-1 (9), 8-3 (10), 4-2 (13), 8-1 (18),
8-2 (19). 8-4 unquantized. All 24 lag frames are load/boot frames. (A first draft of this entry
had 1-2 at 1 frame — wrong phase; corrected the same session.)

**Next.** P0.5 (timing model doc from the code paths — most of the numbers are now in hand),
P0.9 (check whether the community already proved 1-1 optimal at its framerule), then the
fast core (P1.1) and the 1-1 search (P2.1). Track B unit P0.6 stays in the top 5.
## 2026-08-21 — Session 2 (cont.): P0.5 done — timing model
**Did.** `docs/timing-model.md`: NMI/lag, timers, boot/Start, area loads (154+w law derived task
by task from a load trace), game timer, flagpole levels (glitch condition Y ≥ $A2 via
`FlagpoleRoutine`; T_set = grab + T + 159), pipes/sub-areas, 8-4/axe. Facts F31–F34; H19
confirmed for this boot; H21 rewritten as a concrete search objective.

**Learned.** The 1-1 control start (row 197) is locked by the boot ITC phase — Start rows 34–43
are equivalent. The flag-level end sequence is constant except the grab frame and the clock T
(countdown T+1, raise 32, walk 126 in 1-1/4-1/8-1). Pipes are always 48 frames; sub-area
entrances are not framerule-bound.

**Next.** P0.9 (community claims — is 1-1's missing frame known impossible?), P0.6 (warps/area
loading, Track B), P1.1 (fast core).
## 2026-08-21 — Session 2 (cont.): P0.9 done — community claims
**Did.** Read #2964S/#2362S and their threads, thread 1337 pp. 57/59/60/62/63, UserFiles, Maru's
page, six speedrun.com threads/guides (via the r.jina.ai proxy — speedrun.com and
web.archive.org block direct fetches). Wrote `docs/community-claims.md`; facts F35–F37 (S);
H21 annotated (no proof exists), H23 re-ranked, H25/H26 added.

**Learned.** The community has known since 2009 that 1-1 is "1 frame short" and calls it
impossible, with only a naive brute-force size estimate as argument; the WR deliberately loses
time before the 1-1 pole for an FPG-feasible subpixel. 4-2's true gap is 2 frames on the
top-floor route (HappyLee). 8-3: FPG with timer 242 is 3 frames faster (7 left). 8-4: Maru's
RTA-rules TAS has a 1-frame turnaround-room idea to check against the WR.

**Next.** P0.6 (warps/area loading — Track B), P1.1 (fast core), then P2.1 on 1-1 with the FPG
subpixel condition built into the objective. Still to mine: thread 1337 pp. 1–56/58/61, Maru's
movie file, Sockfolder's FPG subpixel analysis.
## 2026-08-21 — Session 2 (end): P0.6 checkpointed
**Did.** Started P0.6 (warps/area loading). Read `ScrollLockObject_Warp`, `WarpZoneObject`, the
pipe-entry world lookup, and the ROM bytes after `WarpZoneNumbers`. Recorded in H5: WZC = 7 would
read `GameTextOffsets` and set WorldNumber 255/255/38 (left/middle/right pipe).

**Next session.** Resume P0.6 from the STATUS checkpoint: (1) dump check — in 4-2 rows
7590–7724 does `WarpZoneObject` (enemy slot) still exist when the text object sets WZC = 6, and
what Y parity/scroll-lock ordering would make it increment afterwards; (2) read
`LoadAreaPointer`/`GetAreaDataAddrs`, `WorldAddrOffsets` (OOB for world 38/255),
`AreaAddrOffsets`, the enemy jump table + Bowser-replacement table, the warm-boot check
($07FD/$07FF); (3) write `docs/warp-model.md`. Session ended at the user's request; all work
committed.
## 2026-08-21 — Session 3: P0.6 done — warp & area-loading model
**Did.** Finished P0.6 from the checkpoint. Read `HandlePipeEntry`, `VerticalPipeEntry`,
`ParseRow0e`, `LoadAreaPointer`/`GetAreaDataAddrs` + tables, `InitializeArea`/`InitializeMemory`,
`PlayerLoseLife`/`ContinueGame`, `PlayerEndWorld`, `Start`, the enemy init/run jump tables,
`BowserIdentities`, the area-object decoder/jump table and the loop command. Wrote
`tools/warp_tables.py` (pattern-locates the ROM tables, prints every WZC×pipe lookup and bogus-world
pointer), `tools/area_data.py` (decodes enemy + level data incl. the row-$0E area-change
commands), `tools/ram_trace.py` (per-frame symbol trace of the full-RAM dump). Wrote
`docs/warp-model.md`, `docs/experiments/P0.6-warp-model.md`; facts F38–F44; H5 refuted,
H6/H13 refuted at table level, H7 sharpened, H15 annotated.

**Learned.** WZC at a pipe is always one of {0,1,4,5,6} (code-level proof): world 8 is reachable
only from 4-2's $2F zone (vine or the wrong warp the WR already uses). Pipe destinations are the
last matching row-$0E command — all 58 tabulated; the Bowser-room page is written only by 8-4's
water section. Completion = axe with WorldNumber ≥ 7. The Minus World ($01 Water2) is a closed
loop at table level. 4-2's "wrong warp" is the page-5 pipe taken before the coin-room command is
parsed. Nothing in the warp/area system beats the WR's structure; Track B gains must come from
memory writes (H7 targets: $075F ≥ 7, $0750/$0751 = $65/16, $06D6 ∈ {2,6}).

**Next.** P1.1 (fast core) is the top unblocked unit; P0.8 (prior tools survey) and P0.7 are the
small Track C/B items. P3.1 now has a concrete target list.
## 2026-08-21 — Session 3 (cont.): P1.1 done — QuickNES harness syncs the WR
**Did.** Cloned/built libretro QuickNES (`tools/build_core.sh`, gitignored `third_party/`), wrote
`src/fastcore/harness.c` (dlopen harness: env/input callbacks incl. `quicknes_up_down_allowed`,
per-frame RAM dump, savestate round-trip bench), `tools/fm2_to_inputs.py`, `tools/compare_ram.py`
(offset search, ignore ranges, all-rows mode). Scanned input-skip × row-offset to find the
alignment, then compared all 17.8k rows.

**Learned.** QuickNES is frame-exact on the WR (F45): identical RAM on every row after boot except
2 OAM bytes on the post-Start lag frame (mid-NMI snapshot), same lag rows, axe on the expected
row. Alignment: FCEUX row r ↔ QuickNES row r−3; FCEUX applies fm2 record j in row j+2 (resolves
the Start-row loose end), QuickNES needs `--input-skip 2`. Speed (F46): 15.0k fps/instance,
104k fps aggregate on 12 threads, 12.8 KB states at 2.5 µs per save+load. `emulate_skip_frame`
(no rendering) is available in Nes_Emu but not through libretro → P1.1b.

**Next.** P2.1: search engine v1 on 1-1 (in-process core, savestates, RAM-hash dedup, threshold
objective from H21). Small units P0.8/P0.7 remain; P1.1b/P1.2 when the search is CPU-bound.
## 2026-08-21 — Session 3 (cont.): P2.1a — BFS engine v1, 1-1 third-room probe
**Did.** Wrote `src/search/bfs.c` (in-process QuickNES, per-layer RAM-hash dedup, 16 A/B/L/R inputs,
terminal evaluation to T_set, deadline pruning with a sound ≤2/frame speed bound and an aggressive
greedy-ground bound). Verified the evaluator on the WR (grab 1285, T_set 1814). Measured the
explosion from the third-room load; analysed the WR's acceleration profile and the pole approach
from the dump; read the horizontal physics (`X_Physics`, `ImposeFriction`, `MoveObjectHorizontally`,
`HandleClimbing`, `BlockBufferCollision`). `docs/experiments/P2.1a-bfs-engine.md`; F47–F49; H21
restructured; H27 added.

**Learned.** Full-state BFS is hopeless at 12.8 KB/state: ×5 per layer, >245k states 6 frames into
control, and the sound bound prunes nothing (its frontier reaches the pole 8 frames before the WR;
the WR is 18.7 px inside it). Pure ground running cannot reach the pole by frame 1284 — the WR's
L+R-facing jump start (doubled adder in the air to 24, Left-tap doubled $E4 to 40) is essential.
The third room is a fixed puzzle (X 2616, speed 0 at entry); the WR stops 5 frames at the pole
base for the FPG. Next leverage: a flat-world frontier (sound relaxation) and the exact FPG
trigger condition (cheap, on this core), and a physics-level core (P1.2) for room-scale search.

**Next.** P2.1b (flat-world frontier + FPG condition), then P1.2 / P0.8 / P0.7 per STATUS.
## 2026-08-21 — Session 3 (cont.): P0.8 done — prior tools survey (while the P2.1b job runs)
**Did.** Web survey (TASVideos 8431/14693/5862S/20204, GameResources, speedrun.com 75044/beov8,
GitHub). Cloned MrWint/smb-opt into `third_party/` and read its state/emu/heuristics/case files.
Wrote `docs/prior-tools.md`; F52; H21/H22 annotated; community-claims updated; STATUS: new unit
P1.2-lite (build + validate smb-opt's model, reuse its XPosHeuristic bound).

**Learned.** MrWint's tool is exactly the "physics-level core" P2.1a concluded we need: 10–12-byte
player-only states, IDA*, precomputed exact x/y-gain heuristics (the sound tight bound), enemies
ignored, segment searches chained by hand — including a 174+59-frame two-segment 1-1 third room,
never a single search from the fixed entry. No whole-level or full-state search exists anywhere.
Maru's best 1-2 is 5 frames short, not 8.

**Next.** P1.2-lite (needs a Rust nightly in the toolbox); P2.1b job result; then the flat-world /
whole-room search with the sound bound.
## 2026-08-21 — Session 3 (end): P2.1b/P1.2-lite checkpointed, job v4 running
**Did.** Parallel compact-state BFS (`src/search/bfs_par.c` v3: template+RAM states, varying-address
compression, forked workers) verified against v2; exported MrWint's XPos table from smb-opt and wired
it in as a sound x bound; added a best-case-descent y bound; found and documented the template
caveat at lag frames (F50). Pole search from the WR's frame-1229 state: v2 hit 1.52M states at
frame 1243 with no grab ≤ 1284; restarted as run v4 with all bounds (running at session end).
smb-opt's own W11PipeSpeedup reproduced (174 frames). F54; experiment files updated.

**Learned.** The x bound is now exact-model-tight (every real-game x-class was in the table); the
remaining growth (×1.4–1.8/layer) is y/subpixel variety, which only the descent bound and the
deadline cut late. The model+core hybrid works: model for bounds, core for truth.

**Next session.** (1) Read `runs/P2.1b-root1229-v4/stdout.log` (see STATUS Running jobs). (2) Depending
on the outcome: full third room from root 1040 (P2.1b), or widen roots; consider the cloud box for
memory. (3) Decide P1.2-lite's enemy question. User asked to end the session here; no new units taken.
## 2026-08-21 — Session 4: P2.1b-m — the model answers the pole-approach question; model validated
**Did.** Checked the core job v4 (killed by the OOM killer at layer 18 together with a model run of mine —
the crash the user saw). Wrote `smb-opt bfs11` (model-side layered BFS with global dedup + MrWint's
bounds; compact storage after the OOM: 2.2 GB for 55M states). Read `FlagpoleRoutine`/`FlagpoleSlide`/
`ProcClimb`: only a Y ≥ 162 grab is fast (F55). Wrote `tools/model_difftest.py` (core vs model on random /
WR-mutated inputs): the model as cloned diverged on 53/200 trials — `NoRunningTimer` and jumps on a held A;
fixed both (`WithRunningTimer`, new `a_held` state bit) → 0 differences on 82,524 frames, 596 grabs, 71
core-confirmed FPG grabs (F56). Searched the pole approach from the WR's frame-1229 state: no glitch grab
≤ 1284 (F57, H27 refuted there). Decoded the third room's enemies (goomba pair on fixed trajectories, F58)
and the collision/stomp rules (F59). Exact x-bound from the room entry: frame 1278 (WR 1280).

**Learned.** The player model + a BFS keyed on the 11-byte player state is ~1000× cheaper than the core
search (38.7k vs 667k states at the same layer, seconds vs minutes per layer) and exact where validated;
the core is the oracle, the model is the search engine. Relaxations are worth stating: the as-cloned model
is a superset of the real game under input remapping, so its "no grab" was already a proof. Memory is the
binding constraint on the 15 GB box — one search at a time, under `ulimit -v`.

**Next.** P2.1b-m2: goombas in the model (F59), validate from the first control frame, then the whole third
room from frame 1045 with deadline 1284 — the first single search from the fixed entry.
At session end the exact-model whole-room probe from frame 1045 is running under a memory cap (×1.19/layer
at frame 1070); the exact-model root-1229 run was stopped at frame 1277 (182M states) — the relaxed model's
run is the proof.
## 2026-08-21 — Session 4 (cont.): P2.1b-m2 — goombas modelled; pole mechanics; whole-room search sized
**Did.** Added the goomba pair to the model (`room_enemies`), a relaxed case + held-A switch for proofs,
`trace11room`, `bfs11 --goombas`, `--check-path`; validated with the difftest from the first control frame
(three bugs found by it: collision parity, goomba position law, and the trace parser dropping L+R-facing
rows) → 0 differences on 97k frames incl. 119 deaths and 35 glitch grabs. Ran search controls: 15 steps
before the WR's grab → none; 16 → 2,256 grabs incl. the WR's. Read the WR's real pole finish from the trace
(land beside the base block from above, L+R jump, grab rising at Y 164) and why nothing simpler works (F60).
Whole-room searches (exact and relaxed+goombas) died at the memory cap at frame ~1092 with 25–27M states
per layer (F61). Docs: F56 updated, F58/F59 corrected, F60/F61, H28; P1.2-lite closed.

**Learned.** The differential tester is the most valuable tool in the repo: every model bug so far was found
by it in minutes. The WR is on the exact x-frontier at the staircase top and optimal from there; the only
remaining 1-1 lever in the room is the handoff state at the stairs (fractions/timers), which the whole-room
enumeration covers but at ~10⁸ states per layer — an engine problem (compact per-layer frontier, ~10
core-hours) or a memory problem (64 GB box), not a physics problem any more.

**Next.** P2.1b-m3: compact per-layer engine (or the cloud box), relaxed model + goombas from the entry with
deadline 238; then exact-model candidates replayed on the core. Track B unit P0.7 still waits.
## 2026-08-21 — Session 4 (end): P2.1b-m3 checkpoint — compact engine built, whole-room run launched
**Did.** Key decompressor (exact inverse of MrWint's bit packing), compact per-layer parallel engine
(`bfs11c`/`bfs11cr`: sorted 16-byte records, chunked sort+dedup, 12 threads, layer files), controls passed
(WR's grabs at step 16, none at 15). Slack-scaling probes: millions of states per layer even at 1 frame of
x-slack (the variety is jump phase × speed fraction × x subpixel, not the y fraction, which every jump
clears). Found and fixed a heuristic panic on goomba-bounce y-substates. Launched the whole-room run
(relaxed + goombas, deadline 238) under a memory cap; it was at 14M states/layer (×1.36) at frame 1092 on the
first try. Path reconstruction from the layer files still needs an offline mode (LSB-first bit order).

**Next session.** Read `runs/P2.1b-model/room_compact_d238.log` (STATUS Running jobs). If it ended with a
grab: write `bfs11c-path`, rebuild, reconstruct, replay on the core (`build/harness` + `tools/model_difftest.py`
machinery). If "no grab": H28 refuted in the relaxed model → 1-1's third room cannot gain the frame; record
the proof and move to rooms 1–2 of 1-1 (entry frame of the third room) or to 8-4/4-2 per PLAN. If it died:
memory engineering or the cloud decision. Track B unit P0.7 still waits.
## 2026-08-21 — Session 4 (cont.): P0.7 done — input semantics catalog (while the whole-room run computes)
**Did.** Read `ReadJoypads`, `PlayerCtrlRoutine`, `OnGroundStateSub`/`JumpSwimSub`/`ClimbingSub`,
`X_Physics`, `ImposeFriction`, `PauseRoutine` and the NMI timer gate; wrote `docs/input-semantics.md`; F62;
H3 annotated. **Learned.** L+R/U+D are never masked; L+R = facing 3 (doubled friction, no run cap on the
ground, Right wins); a pause costs ≥ 44 frames, freezes every timer and the frame counter and all logic
but still steps the RNG — a pure RNG lever (8-4 Bowser / Hammer Bros), useless for framerules. The 16
A/B/L/R inputs are complete for small Mario on land (Down = release L/R; Up only on vines).
**Next.** Check the P2.1b-m3 run (STATUS Running jobs).
## 2026-08-22 — Session 4 (late): segment comparison — the WR equals MrWint's enemy-free optima in every 1-1 segment
**Did.** Read the WR's room boundaries from the dump and compared with `w11.rs` solution lengths: 368/111/174
all equal (F63); bonus room therefore proven optimal; H29 (bounce-assisted room 1) recorded. Built
`bfs11c-path`; run 3 of the whole-room search launched with an RSS watchdog. **Next.** Run 3's verdict
(STATUS Running jobs); then H29 needs the room-1 enemy model (goombas + green koopa).
## 2026-08-22 — Session 4 (late): P3.1 done — static OOB audit
**Did.** `tools/oob_audit.py` + `docs/oob-audit.md`. **Learned.** No indexed/pointer store reaches the H7
cells; every JumpEngine index is engine state or a ROM-bounded enemy ID — except `EnemyFrenzyBuffer`, which
the block-buffer wrap write (objects above the status bar, y → $E0/$F0) can reach from an odd page at column
11 — and the vine writes $26 there as it grows (H30). Track B has a concrete code-execution-candidate to test
on the core (P3.3). **Next.** P2.1b-m3 run verdict; then P3.3/H30 or H29 depending on it.
## 2026-08-22 — Session 5: run 3 OOM post-mortem; external-memory engine; run 4 resumed from layer 85
**Did.** Run 3 reached layer 85 (328M states, 741 s/layer, growth ×1.024 and flattening) and was killed by the kernel
OOM killer at 11.1 GB RSS (the 10-s MemAvailable watchdog never fired; the pressure also crashed the Claude Code
session). Root cause from the code: parents + 12 unbounded accumulators + merged `next` (with Vec doubling) all
resident per layer ⇒ ≥ 15 GB at 328M states. Rewrote `bfs11c` as an external-memory engine (streamed parents,
bounded accumulators spilled to sorted runs, k-way merge into the next layer file, `--resume`, `--stop-step`, FxHash
heuristic maps); validated: 16-step control identical incl. path reconstruction, resume-from-layer-40 reproduces run
3's layer counts 41–46 exactly at 1.8× speed, 649 MB peak. Run 4 resumed from `layer_085.bin` inside a systemd scope
with `MemoryMax=10G` (verified the cap applies without sudo). Patch regenerated; launch scripts copied to `tools/`.
**Learned.** Polling watchdogs cannot catch multi-GB allocation bursts; cgroup caps can, and keep the rest of the
system (and the agent session) alive. Per-layer dedup is set-deterministic, so resumed runs are checkable against
the old log to the last digit — the cheapest possible regression test for an engine rewrite. The cloud is not
needed for this unit (fits in 10 GB, ~1 day); no provider credentials exist on the laptop.
**Next.** Run 4's verdict (STATUS Running jobs): candidate → reconstruct + core replay; no grab → H28 refuted in the
relaxed model, P2.1b done, then P2.5 (enemy-aware segment search; H29 room 1) and the Track B unit P3.3/H30.
## 2026-08-22 — Session 5 (cont.): P2.5a — 1-1 room-1 enemy rules read and validated (while run 4 computes)
**Did.** Split P2.5 into P2.5a (room-1 enemy model) and P2.5b (searches); scanned the WR for every stomp (two in
1-1 room 1 — rows 323 and 517 — one in room 3, the rest from 1-2 on); decoded room 1's enemy data (goombas A/B +
a pair; the koopa is past the pipe); read the spawn law (`ProcessEnemyData`/`CheckRightBounds`: ScreenLeft + 303 ≥ x;
groups placed at ScreenRight), the walk (`MoveObjectHorizontally`, stale move force), the pipe turnaround
(`DoEnemySideCheck`), enemy–enemy turnaround (`EnemiesCollision`), the flattened-goomba lifetime (`ChkKillGoomba` at
interval-timer 14), offscreen erase, and the scroll law; wrote `tools/room1_enemy_sim.py`, which reproduces the WR
dump's enemy slots exactly on all 369 room-1 frames (0 mismatches, both stomps predicted) and fails correctly under
perturbations. F64/F65 (F59 corrected: stomp keeps the X speed), H29 in-progress, experiment file.
**Learned.** Room-1 enemies are not frame functions: spawn frames follow the scroll (Mario's path), the pair's x is
ScreenRight at its spawn frame, and slot reuse carries the half-pixel phase — the search state must carry a few
bits per enemy plus the scroll. `AreaParserTaskNum` blocks spawns one frame in eight-ish (scroll-history dependent).
**Next.** Port the rules into the smb-opt patch (room-1 case with `WithScrollPos`), difftest from row 197, then the
deadline-367 search (P2.5b) once run 4 is done.
## 2026-08-22 — Session 5 (cont.): P2.5 scan — the WR sits on every known segment optimum; 8-4 at the cap
**Did.** Compared the WR's segment times with MrWint's solved cases on the route (1-2 opening, 8-4 speedups and both
pipe clips): gap 0 everywhere (F66); profiled 8-4 frame by frame — speed 40 on every frame of all room middles
(incl. the 445-frame loop section), water room at the swim cap for 667/696 frames, Bowser room 246/278 (F67).
`docs/experiments/P2.5-segment-scan.md`; H23/H24 annotated; STATUS: P2.3a (4-2 top route, 2 frames short, no
existing bound) queued ahead of the room-1 enemy port; H29's prior noted as low (bounce = fixed −4 y speed).
**Learned.** HappyLee's 2011 inputs are player-optimal wherever an exhaustive bound exists; the unexplored
running room is exactly the five levels nobody searched (4-1, 4-2, 8-1, 8-2, 8-3). 8-4's unquantized frames
cannot come from running.
**Next.** Run 4's verdict (tomorrow morning); then P2.3a.
## 2026-08-22 — Session 5 (end): P2.3a checkpoint — 4-2 timeline and exact block maps from the dump
**Did.** WR's 4-2 segmented (main area 588 on the bottom route, warp zone 476 over the screen top); wrote
`tools/blockmap_from_dump.py` (level metatile map from the two block buffers as the renderer passes; columns valid
from the entrance page to the renderer position, read on parser-idle frames) and validated it cell-for-cell on
MrWint's BB11/BB12; extracted 4-2's main area and warp zone (`data/blockmaps/`); decoded 4-2's enemies; wrote the
step-3 plan (cases, goal coordinates, generalized search mode, difftest alignment) into STATUS.
**Learned.** The dump is a complete, exact source for level geometry — no area-object renderer needed; a mid-level
entrance leaves stale zeros in the unrendered buffer half, so validity must start at the entrance page.
**Next.** Run 4's verdict; P2.3a step 3 (cases + enemy-free optima for 4-2's two segments).
## 2026-08-22 — Session 5 (late): user Q&A → P1.3 queued, model-omissions table, H31
**Did.** Answered the state-completeness and x-bound-soundness questions; queued P1.3 (audit the XPos table against
the real core with random k-frame rollouts; cheap, spare-capacity job) ahead of the 4-2 search; added a standing
"Model omissions" table to STATUS with the lift/platform gap flagged as the one mechanic that breaks the x-bound;
H31 records the user's framing: cracks live in unmodeled mechanics.
## 2026-08-22 — Session 5 (late): P1.3 done — x-bound audited against the real core
**Did.** `smb-opt trace11bound` (per-step max-gain vector from the search's own classifier) + `tools/heuristic_audit.py`
(random core rollouts vs the bound): 1.9M checks, 0 violations, 0 unknown classes, bound tight; F68; patch regenerated.
**Learned.** The pruning bound is not the crack. What remains unmodeled (lifts, shells, bumps, swimming) is.
## 2026-08-22 — Session 6: P2.3a step 3 — 4-2 in the model, three MrWint-model bugs fixed, warp zone exact
**Did.** Run 4 checked (layer 122, ~900 s/layer, ETA slipped to ~Aug 23 late / Aug 24). Added BB42/BB42Warp, `W42Main`/`W42Warp`
cases, case-generic `tracec`/`bfsc` modes and `model_difftest.py --case`. The WR trace exposed the alignment law (row = record+2,
F69) and three model bugs, each read from the disassembly and verified on the dump: the block-bounce timer on head bumps
(F70), the water-only joypad-disable rule (F71), coins ending the collision routine (F72). Added `Options::BlockBounce`
(default off — existing cases and run 4's layer keys unchanged) and coin-list handlers. Warp zone now frame-exact on the
WR + 30k random/mutated frames; main area exact to the lift, which the WR actually rides and jumps off (F73 — the earlier
`PlatformCollisionFlag` check was the wrong flag). Pipe-entry rule and X windows (F74). Full-input BFS explodes even with
1 frame of slack while MrWint's reduced-input IDA* solves the 1-1 control in 22 s (F76); IDA* on the warp zone running.
**Learned.** The WR is a better model test than random inputs: it visits the mechanics a fast route needs (brick bumps,
coins, above-screen jumps, the lift). Run-4-safe extension pattern: associated-type defaults on `Options`. `pkill -f`
patterns must not appear in the calling shell's own command line (killed my own shell twice).
**Next.** P2.3b: lift + scroll in `W42Main`, difftest to 0; search strategy for the slack problem (external-memory `bfsc`,
or a y-aware admissible bound, or chokepoint segmentation); read the IDA warp result.
## 2026-08-22 — Session 6 (cont.): P2.3b — the 4-2 lift modeled; two more laws fixed; a 1-frame pipe gain verified on the core
**Did.** Lift hook (spawn from the parser law, descent, bbox collision → land/bonk/side push, rider placement, erase) in
`tracec`/`bfsc`/difftest; `W42Main` tracks the scroll; fixed MrWint's scroll timing (F77), derived the AreaParserTaskNum law
(F78). Main area now exact on all 587 WR frames incl. the ride; 120 near-lift mutated trials clean except enemy deaths and
bumped-block states. Found and verified on the core that HappyLee's 4-2 pipe entry is 1 frame late (F79; `tools/pipe_entry_scan.py`
checks all 7 WR pipe entries). Understood the bottom route: a floor-level walk inside the brick block via the side-check early
return (F80). Block states ($23/$c4) are the last main-area model gap (P2.3b-2). Search control: plumbing OK, frontier explodes
(P2.3c).
**Learned.** Validate with WR-mutated trials near the mechanic (every trial touched the lift), not uniform random ones. Two
lift bugs (kept y fraction; offscreen box) only showed up that way. `pkill -f` self-kill: isolate the kill in its own call.
**Next.** P2.3b-2 (block states) or P2.3c (search slack) — P2.3c first: without it no 4-2 bound can be computed at all.
## 2026-08-22 — Session 6 (end): P2.3c measurements
**Did.** `bfsc --reduced` (MrWint's input set): the 1-1 proof space is only ~2× smaller (F82) — IDA\* is fast by finding, not
by a small space; proofs need the external-memory engine. Read the WR's warp-zone route: roof run, drop at x 958, 150 px back
to the pipe (F83) — the x-bound's 147-frame slack is structural; a staged landmark bound (overshoot + return) would cut it to
~20–30. P2.3c refined in STATUS into concrete sub-steps.
**Next.** P2.3c-1: generalise `bfs11c` (external memory + `bfs11c-path`) to any case + hook; P2.3c-2: staged bounds per
segment (warp: overshoot/return; main: pipe-A/brick/pipe-B gates); then P2.3b-2 block states and the enemy models (piranhas,
goombas, koopa) before any 4-2 bound is claimed.
## 2026-08-22 — Session 7: P2.3b-2 done — block states in the 4-2 model; an uncapped control OOM-killed the session
**Did.** Read `PlayerHeadCollision`/`BumpBlock`/`BlockObjectsCore`/`BlockObjMT_Updater`, the NMI flush, `ColorRotation`,
`RunGameTimer` and the parser task table; measured on the dump: `$23` for 14 frames, restore on the 14th only when
`VRAM_Buffer1` is empty, which the column renderer (`AddrCtrl` 6), coin erases, the palette rotation and the game-timer
digits can block (F84–F86). Added `Options::BlockStates` (56-bit `State.blocks`: bounce cell, `$c4` mask, coin-brick
timer, a mod-168 frame phase, parser task/column, VRAM flags) with `W42MainBlocks` (16 cells). `tools/block_state_check.py`
compares every bookkeeping field with the dump: 0 mismatches on 587 rows; difftest: WR + 100 random + 240 mutated
block-bumping trials, 0 block-related differences (F87). The WR itself bumps the mushroom brick, a question block and the
vine brick. H34 (item routes) recorded. Capped `bfsc` control: WR suffix in the frontier, 20-byte key OK.
**Crash.** The first plumbing control (`bfsc … 540 587 --check-path 47`, in-memory frontier, uncapped) was OOM-killed at
20:09 and took the Claude Code session with it; run 4 survived (its own cgroup). Rule added to STATUS and memory: every
search — controls included — runs under `systemd-run --user --scope -p MemoryMax=…` with absolute paths.
**Learned.** "When does the block come back" is a VRAM-scheduling question, not a physics one; the dump answers it in
minutes (`tools/ram_trace.py` on `VRAM_Buffer1`/`AddrCtrl`/`AreaParserTaskNum`). Combining the 8/21/24-frame phases into
one mod-168 counter keeps per-layer-deterministic state out of the dedup cost.
**Next.** P2.3c-1: generalise the external-memory engine (`bfs11c` + `bfs11c-path`) to any case + hook (`bfscx`),
then the staged bounds (P2.3c-2); the big runs wait for the cloud decision. Run 4 ETA ~2026-08-24 early morning.
## 2026-08-22 — Session 7 (late): P2.3c-1 done — `bfscx`, the external-memory engine for any case
**Did.** Generalised `bfs11c`/`bfs11c-path` into `bfscx`/`bfscx-path` (any `SmbSearchCase`, object hook + ext in
24-byte records, the case's `SearchGoal` as bound and goal, `--check-path` by binary search in the sorted layer files).
Controls under `systemd-run` caps: 4-2 WR suffix (prefix 575, deadline 587) — layer counts identical to `bfsc`, the WR in
the frontier at every layer, goal at layer 10, path reconstructed and **replayed on the core: pipe entry at frame 7166,
3 frames before HappyLee** (F88; framerule-absorbed); 1-1 room 1 (deadline 368, 40 layers) identical from layer 22 on,
earlier layers differ by per-layer vs global dedup. `tools/replay_check.py` replays any reconstructed path on the core.
**Learned.** The generic engine costs nothing over `bfs11c` (21 s either way on the control); per-layer dedup is the
right semantics for frame-indexed searches and makes resumed runs checkable to the digit. The first "better than the WR"
search result came out of a 12-frame plumbing control — HappyLee brakes before the 4-2 pipe.
**Next.** P2.3c-2: staged admissible bounds per segment (warp zone: overshoot/return; main area: pipe-A/brick/pipe-B
gates) in the cases' `SearchGoal`, each checked with `--check-path` on the WR and the F68-style audit; then the runs
(cloud decision pending).
## 2026-08-22 — Session 7 (end): P2.3c-2 — the warp-zone bound: 329 → 461 of the WR's 476; the proof still needs the cloud
**Did.** Ext-aware bounds (`SearchGoal::distance_to_goal_heuristic_ext`, `--stage` phase hook: ext = 1 once X ≥ 957,
the only way under the roof); `W42Warp`'s staged bound (approach + C_RET return, speed-cap y parts) and the coupled
two-phase x bound (`build_overshoot_bound`: end-class-restricted max-displacement DP, 11 s to build after indexing the
class graph). Root bound 461 (0 violations along the WR); the WR's slack (15) sits entirely in the final ~100 steps.
Exhaustive controls from the WR's drop state: 76 optimal, 75 impossible (F90). Frontier growth still ×1.25/layer at
layer 24 (9.2M) — F91. One mistaken run (deadline counted from the prefix root) reached 102M states before I killed
it; two `pkill -f` self-kills (the pattern was in the same command line — isolate kills, as the memory note says).
**Learned.** An x-only table cannot see the drop/fall/landing coupling; the y-table is unsound for descents (bonks).
Even a zero-slack phase carries 2×10⁷ states/layer here, so bounds alone never make 4-2 laptop-sized: the proof runs
are cloud jobs, and the bound's job is only to keep the layers flat.
**Next.** P2.3c-2b (end-game (x,y) bound or the Phase-B multi-root search, H35) and P2.3c-2c (main-area gates); then
the cloud decision for the runs. Run 4 ETA ~2026-08-24 early morning.

## 2026-08-22 — Session 8 (interleaved): P0.10 — cloud provider, billing mechanics, machine sizing
**Did.** Installed `hcloud` 1.67.0 to `~/.local/bin` from the official tarball (no sudo, no toolbox); the user
created context `smb1-tas` in their own terminal — `hcloud context create` needs a TTY and fails under Claude
Code's `! …` with `non-interactive tty detected`. Verified against the API (`hcloud location list`, exit 0).
Established the billing rules from Hetzner's docs + the authenticated pricing endpoint (F95): hourly rounded up,
monthly cap, ancillary rates — and the one that matters, **a powered-off server still bills; only `delete` stops
the charge**. Measured the engine's scaling limit from run 4's own log (F96): expansion is parallel over
`--threads`, the k-way merge is single-threaded, serial fraction 4–6 % at 12 threads → the useful ceiling is
~48 cores. Since $/core-hour is flat across dedicated tiers, the $300 cap is really ~9,000 core-hours and
machine size buys wall-clock only. **Then the user hit the account quota**: new account, only ccx13/ccx23/ccx33
(≤ 8 dedicated cores), and the console refuses a limits-increase request as the account is too new — which
inverts the recommendation, because 8 dedicated cores is ~1.08× the laptop. Rewrote the analysis around that.
`docs/experiments/P0.10-cloud-sizing.md`; STATUS Spend now carries the standing cloud rules.
**Learned.** Price the *quota*, not the catalogue — the sizing answer (ccx63) was worthless the moment the
account limits appeared, and the rewrite is the real deliverable. Two things survived the inversion and are
worth more than the original answer: the shared tiers are **4–10× cheaper per core** (cx53: 16 cores at
$0.0561/h vs ccx33's 8 at $0.2612/h) and can be benchmarked for under $1, and at ≤ 16 cores the serial merge is
irrelevant, so P2.3c-3 (parallel merge) is parked rather than queued.
**Next.** P0.10a — benchmark cx53 / cpx51 / ccx33 against the laptop's logged throughput (~$0.46, delete same
hour); check whether shared tiers are quota-limited too. Run 4 stays on the laptop (ETA ~2026-08-24 early
morning). Re-request the Hetzner limits increase once the account has history — that is the gate on the 4-2
main-area proof run. Unchanged: P2.3c-2c is still the in-progress unit.
## 2026-08-22 — Session 8 (alongside run 4): P2.3c-2c started — where the 4-2 main-area bound is loose; top-route reference via segment searches
**Did.** Run 4 checked (layer 142, ~1000–1400 s/layer, ETA 2026-08-24 morning). Measured the x-only `W42Main` bound along
the WR (`--check-path 588`): root 540 vs 588; slack 46 → 36 in the entrance fall, 35 → 4 in the col-30 wall entry
(steps 201–221), tight elsewhere (F94). Read the geometry exactly (F95: the pillar is rows 7–9 with an open row 10 — the WR
runs *under* it; pipe B is a floor-to-row-4 wall) and the wall-entry mechanics from the model trace + disassembly (F96: a
Left press turns the foot-check impede into a +1 px push into the wall). Decoded the enemy data: `$3A` at col 46 = **3
goombas on the Y-112 top floor**, the route HappyLee calls 2 frames short — they are not in the model. Added `bfscx
--goal-x PX [--goal-y PY]` (position goals, x-table bound, best-of-layer goal pick; regression control identical),
`tools/bfscx_ladder.sh` (deadline ladder: a position-goal BFS only stays small at the segment optimum — deadline +28
doubled the frontier per layer), `tools/chain_inputs.py`. Segment S1 (root → x ≥ 339, Y ≤ 112): deadline 147 dies at
layer 29; 149 running (~9M states/layer, ~100 s/layer at nice 10, 2 threads, 2 GB cap).
**Learned.** The WR's main-area deficit is two localized costs (entrance fall 10, wall entry 31), so the enemy-free top route
should be ≈ 550–555 — and the thing that can make it 577 is the goomba group, which means 4-2 needs the P2.5-style enemy
module before any proof run is meaningful. The x-only bound's remaining looseness is y-variety (heights), not x.
**S1 verdict (late):** deadline 149 reached 23M states at layer 100 still growing (max x ≈ 215 px) and was killed by the
watchdog; 147 dies at layer 29 — the x-only bound keeps every height variant (F95). Reference chain parked.
**Next.** The y-coupled gate terms for `W42Main` (must-land-then-jump law at the pillar top / pipe B, the entrance fall with
air acceleration; spec in the experiment file), checked on the WR and audited, then the S1 ladder again → chain S2–S4 →
core replay. New unit P2.5c (4-2 enemy module: the goomba group, koopa, beetle) queued right behind it — 4-2 is
goomba-limited on the top route. Then the cloud decision (the user wants to discuss the provider next session).

## 2026-08-22 — Session 8 (cont.): P0.10 revised — the auction route, pro-rata billing, and a sizing rule
**Did.** Two corrections to the earlier P0.10 conclusion, both from following the user's questions rather than
my own plan. (1) **The Cloud quota is not the only door.** Hetzner's Server Auction (Robot) has no vCPU-quota
system, **no setup fee, no minimum term**, immediate cancellation, and — the part that changes the maths —
**billing exact to the hour and pro-rata, "you will never pay more than the monthly price"**. So the monthly
figure is a *ceiling*, not a commitment, and boxes must be compared by **day rate**: a 32c/64t EPYC 7502P with
128 GB + 1.9 TB is ~$9.67/day against cloud ccx33's $6.27/day for 8c/240 GB. I had framed €333.70/mo as
"blows the whole cap in a month", which was wrong for a run that lasts days (F97). (2) **Sized the 4-2 run
properly from live data instead of guessing** (F98): the S1 ladder at deadline 149 (2 frames of slack) plateaus
at ~1.4×10⁷ states/layer and *turns over*, 131 s/layer on **two threads**, 90 layers in 41 minutes — fifty
times smaller than run 4's layers. Frontier per layer spans 3 orders of magnitude on the bound's slack, so the
machine decision is premature until P2.3c-2c reports; wrote a decision rule into STATUS so the next session
applies it mechanically. Also fixed a fact-ID collision I created (my F92/F93 → F95/F96; P2.3c-2c had already
taken F92–F94 in the same working tree).
**Learned.** Price the *terms*, not the sticker: pro-rata hourly billing on bare metal makes a "€334/month"
box a $12/day box, which is a completely different decision. And when two agents share a working tree, append
to `docs/facts.md` only after re-reading it — `tail -3` at the start of a unit is stale by the end of it.
**Next.** Unchanged and not blocked on cloud: S1 d149 finishes within the hour (layer 95 of 149 at the time of
writing), then S2–S4 chain per the P2.3c-2c checkpoint. Run 4 at layer 143/238, ETA ~2026-08-24. Apply the F98
decision rule when the full-level frontier is known. Worth de-risking early: whether Robot gates new accounts
the way Cloud does (user action; ordering flow, no purchase needed).

## 2026-08-23 — Session 9: the y-coupled bound (P2.3c-2c), and the 4-2 enemy reference sim (P2.5c-1)
**Did.** (1) `heuristics::ygate` — a sound y-coupled lower bound for position goals `x ≥ GX ∧ Y ≤ GY`: the model's
exact vertical rules relaxed over *surfaces* = every standable cell top of the block buffer with the x intervals where a
foot point is inside its column (wall faces and in-wall rows included, because of F80 and the wall jump), the hold-A
trajectory as the pointwise-highest envelope, per-surface landing bounds with the x table's charge, y-only T(surface)
precomputed top-down, and a per-k join with the x table. Wired into `bfscx --goal-y`; `smb-opt traceh` +
`tools/ygate_audit.py` (300 random trajectories, 1,485 checks, 0 violations); regression control identical. The
pipe-B gate of the session-8 spec was dropped as unprovable (H37: wall-entry mechanics). S1 d149 with the bound is
running detached (identical counts to the x-only run through layer 85 — the term cannot bite before the jump region),
and an S1a ladder (first arrival at the last floor block) in parallel. (2) While those grind, P2.5c-1: a reference
simulation of the 4-2 main-area enemies validated on the WR dump — **0 mismatching rows over all 588 frames**, with
the negative controls biting (119/20/63). It found three **piranha plants** nobody had in the spec, that the
wrong-warp pipe's plant is *slot-dependent* (the WR had all five slots full at col 84; a freer route gets a plant in
the pipe it must enter, F100), and that the enemy loader sees the *previous* frame's `AreaParserTaskNum` (F78
amended; the lift hook was one frame off at burst boundaries — fixed, rebuilt, F81 control re-run). Also fixed:
`tools/bfscx_ladder.sh` (`systemd-run -p Nice=` is rejected for scopes here), `area_data.py`'s import-time argv parsing
breaking the sims when given arguments.
**Learned.** The x-only frontier explosion is *intrinsic* at 2 frames of slack: ~10⁷ distinct hop/sub-pixel variants
per layer are all x-tight, and a y-term only prunes within ~25 frames of the goal — so position-goal ladders cost
hours on 2 laptop threads regardless; the decision rule F98 stands but the "10⁷ → hours" regime is where we are.
Reading the dump beats reading specs: the plants and the slot dependence came from a 20-line slot survey.
**Next.** P2.5c-2 (the Rust enemy module for `W42Main`, with slot occupancy) is the decisive work for H36; the S1/S1a
results feed the reference-path chain (S2–S4) when they land. Run 4 ends ~2026-08-24 00:30.
**Later (session 9, cont.): P2.5c-2 started.** The reference sim ported to Rust (`w42enemies.rs`, 96-byte search records
with a 64-byte object ext; `tracec/bfscx --enemies`), matching the dump frame-for-frame to the vine bump; the remaining
differences are all the unmodelled vine's slot usage (H34) — the stale slot memory (`EraseEnemyObject` keeps the
move force / collision / masked bits / sub-pixel accumulators) turned out to matter for a walker's half-pixel phase and
is now in the record even for empty slots. Three core difftests (`--enemies`) launched for the next session. Process
lesson, twice: a `cd` inside a compound Bash command made later commands run in the vendored smb-opt repo (a stray
commit there, reset) — absolute paths and `git -C` only.

## 2026-08-23 — Session 10: P2.5c-2 step 1b — the enemy module validated on the core; F101; search pruning fixed
**Did.** Read the session-9 difftests (0 differences, but only ~15 goomba contacts). Built region-prefix difftesting:
`tools/w42_prefix_gen.py` (model-generated prefixes that reach a region without item bumps or enemy events) and
`model_difftest.py --prefix-dir/--require-event/--stop-x/--wr-file/--only` with stomp/kick counts and the H34
item-bump stop. The first koopa-region trials exposed **F101**: the player's hitbox is built *before*
`PlayerBGCollision`, so a landing snap or wall push-back in the same frame does not move it (pipe-A plant kill
at f7132, koopa kill two frames later at f7232) — fixed via a per-thread pre-collision position (`emu::pre_bg_pos`).
Then a zero exposed a tool bug (the trace prints ` STOMP`, the tools looked for `Stomp`), and the beetle set showed
the block map ends at col 97 (`--stop-x`). Final: **5,787 trials, 877,058 frames, 0 differences; 1,825 matching
deaths, 3,686 stomps, 949 kicks** (F102) — goombas, koopa/beetle shells and kicks, the three plants, F100's
slot-dependent plant. Found and fixed that the search loops ignored the hook's verdict (enemy deaths were not pruned);
item bumps are now refused in searches (`LiftEvent::ItemBump`); two search controls (the WR suffix is outside the
enemy model because of its vine bump — consistent with F100; a vine-free entry path searches end to end). Patch
regenerated. Run 4 paused with SIGSTOP at 12:28 at the user's request (resume: `kill -CONT 172117`).
**Learned.** Every difference so far came from *ordering within the frame* (F78 loader, F101 hitbox), not from the
rules themselves — read the routine order, not just the routine. A count of zero is a test of the tooling before
it is a fact about the game. Region prefixes + model-filtered continuations give 100× the event density of random
inputs from the root for the same core time.
**Next.** P2.5c-2 steps 4–5: the ygate bounce relaxation (stomps give −4 y speed: the y-bound must admit them),
then the enemy-aware S1→S4 chain / main-area run; d149 (enemy-free S1) still running under its watchdog.

## 2026-08-23 — Session 10 (cont.): the bounce relaxation (P2.5c-2 step 4), and S1 solved = 149
**Did.** (1) The ygate bounce relaxation: a bounce band pseudo-surface at Y 102 (the highest a stompable 4-2 enemy
can be under Mario), x-gated on the group-spawn condition (ScreenLeft ≥ 433 ⇒ x ≥ 433), take-offs = −4 px arcs with
the fall gravity (the asm keeps the down force after a stomp), enabled only under `--enemies`. The audit caught two
bugs before it was right: states already inside the band region couldn't "land" on it, and a latent first-frame
off-by-one in the y-only T tables (any goal within 4 px under a surface top; enemy-free goals never hit it).
Final audits: 0 violations over ~1.6M checks incl. 200k+ stomp-dense ones; the enemy-free S1 bound byte-identical.
`traceh --enemies` added (death stops; ITEMBUMP marks but does not stop — the koopa/beetle prefixes carry the WR's
harmless mushroom bump; the first audit round on those prefixes was silently vacuous because of that stop — read
"reached 0" as suspicious, not as "goal hard"). (2) **The d149 search finished: S1 = 149 exactly** (F103) — goal at
layer 149 with 45.5M transitions, nothing earlier, endgame frontier collapse as designed; `bfscx-path --stride 24`
added (the run's layers predate the 96-byte records; the reconstruction first failed reading 24-byte records as
96), path chained and **core-verified 149/149**. Run 4 was SIGSTOPped 12:28–14:55 at the user's request (the 4-2
work got the CPU) and resumed losslessly. MacBook access confirmed available (`ssh mac`, global CLAUDE.md) — a
horizontal option for parallel segment ladders when wanted.
**Learned.** The audit keeps earning its keep: three real bugs in one afternoon (in-band landing, first-frame
off-by-one, the vacuous-audit trap), all found by reading zeros and violation shapes rather than by difftests.
A paused 12-thread search is a perfectly good way to lend a laptop to a second workload for 2.5 h.
**Next.** The enemy-aware S2 ladder from `chain_s1.bin` (prefix 149): `--enemies 0 --goal-x 755 --goal-y 112`,
8 threads, capped — the first search through the goomba group, and the next piece of the H36 answer; then S3/S4
and the top-route total vs 575.

## 2026-08-23 (session 11, Mac) — P0.11: the Mac as an overflow host

**Did.** Brought the Mac clone up to date (it was 67 commits behind) and confirmed the Fedora
box pushes every commit (`main == origin/main`; only ~7 min of in-flight engine edits at the
time of the check). Measured the Mac as a second host (F105–F110). Designed and documented the
two-machine work protocol as an *addition* to the loop rather than a new topology
(PROCESS.md "Parallel work on the second host", `docs/decisions.md` 2026-08-23). Wrote
`tools/Dockerfile.smbopt`, `tools/mac_run.sh`, `tools/watchdog.sh`; made `tools/build_core.sh`
find `cargo` on PATH (the container's CARGO_HOME is `/opt/cargo`, not `~/.cargo`, so it used
to silently skip the engine build). Synced the five gitignored data files to the Mac.

**Learned.**
- The Mac cannot run `smb-opt` natively and this is a hard wall, not a config error (F107):
  no `aarch64-apple-darwin` build of `nightly-2018-06-01`, and the x86_64 toolchain compiles
  under Rosetta but cannot link — Apple's 2026 linker rejects the 2018 rlib metadata layout.
  `-ld_classic`, `-C prefer-dynamic` and `arch -x86_64` were all tried and all fail.
- The right shape is an arm64 Linux container (F108): native speed, the project's Linux-only
  scripts work unchanged, and `docker run --memory` gives a real cgroup cap — which is the
  Mac's answer to the "never start a search without a cgroup cap" rule.
- **The real hazard of two boxes is not STATUS.md conflicts but `third_party/smb-opt`** — an
  untracked third-party tree whose only channel into the repo is a hand-regenerated patch.
  Hence the single-engine-editor rule. Framing the Mac as opportunistic overflow (rather than
  a co-equal machine with a parent/worker protocol) makes the single-writer property fall out
  for free.
- Cross-machine BFS is not worth building: the LAN is 96.9 MB/s (F110), ~33 min per 190 GB
  layer.

**Blocked.** `docker build` fails on the Mac in every variant tried, including with the base
image local and an empty context (F109). `docker run`, `docker load` and container networking
all work, so this is image *creation* specifically. Two of the four ways out need the user
(Docker Desktop GUI, or `dnf install qemu-user-static` on the Fedora box).

**Next.** P0.11a (unblock the image — needs a user decision), then the control run.

**Note on this session's commits.** Done on branch `p0.11-mac-overflow`, not `main`, because a
Fedora session was working concurrently. Merge deliberately: `docs/facts.md` (F105–F110),
`STATUS.md` and `docs/log.md` are the likely conflicts, and the fact numbers may need shifting
if the other session also appended.

## 2026-08-23 — Session 11: S2 solved enemy-aware — 166 = the movement bound, the goombas are free (F112); S3 running
**Did.** Pulled the Mac agent's P0.11 work mid-session (two-box protocol in PROCESS.md; the Mac is NOT yet operational —
`docker build` hangs there, P0.11a needs the user: Docker Desktop GUI repair or `dnf install qemu-user-static` here).
Run 4 SIGSTOPped 16:40 (user OK'd; **resume `kill -CONT 172117`**) to give the S2 work 8 threads. S2 (first
x ≥ 755 ∧ Y ≤ 112 from `chain_s1.bin`, `--enemies 0`): probe gave root bound 166, and the ladder's **first rung d166
found the goal at layer 166** (70.6M goal transitions, peak frontier 5.54M, 1,996 s) — proof-grade since deadline =
bound (F112). Reconstruction first FAILED: bfscx printed the goal-parent record truncated to klen+2 = 22 bytes (a
24-byte-record-era print), so the 64-byte enemy ext was zero-padded and matched no parent. Recovered the full 96-byte
record from `layer_165.bin` by prefix (3 matches — the goombas in three walk phases), reran, and fixed the print to
emit the full record (engine rebuilt, patch regenerated). `chain_s2.bin` (6,899) **core-verified 315/315 frames, 1
stomp** (x ≈ 690, in stride). S2's 30 G of layers deleted after the verified reconstruction. S3 (→ x ≥ 1005, the
lift pit) probed: root bound 100; ladder `100 2 140` running at 8 threads (`top_s3_ladder.log`). `bfscx_ladder.sh`
gained a `MEMCAP` override and a <40G-free disk guard.
**Learned.** The enemy-aware optimum can *equal* the enemy-free movement bound — a stomp taken in stride while
already descending costs nothing; H36's "three forced stomps" premise is dead for the group section (1 stomp, 0
frames). Also: every truncation is invisible until an ext is nonzero — print full records, and when a reconstruction
fails, suspect the record before the search.
**Next.** S3 verdict → S4 (the wrong-warp pipe entry; the F100 slot-dependent plant is the open cost question —
if S4 is expensive, test a slot-filling item bump, H34) → `replay_check` core replay of the full chain → the slack
accounting vs HappyLee's 577 → the staged full-level bound. Resume run 4 when the searches are done.

### 2026-08-23 (session 11, Mac) — P0.11a: the Mac is operational

**Did.** Cleared the `docker build` blocker by routing around it: with `qemu-user-static`
installed on the Fedora box, the arm64 image is built there under emulation (~25 min, `nice`d)
and shipped to the Mac as a tarball — the Mac needs only `docker load` and `docker run`, the
two operations that do work (F109). `smb-opt` then builds **natively arm64** in the container
in 1m 59s, and the 4-2 WR-suffix control gate reproduces
`runs/P2.3c/ctrl_w42main_p575_d587.log` **exactly** (F111). Merged the P0.11 branch to main
(`eae7ec2`, clean, both sides' STATUS edits intact).

**Learned / built.** The day-to-day hazard is not the container, it is **engine staleness**:
`third_party/smb-opt` is untracked and reaches the project only through
`tools/smb-opt-modes.patch`, so any pull touching that patch leaves the Mac's binary built from
the wrong source with silently wrong numbers. This actually bit mid-session — the patch changed
in `5bfe55c` while the Mac still had `2a1d15b`'s applied. Now mechanised rather than written
down: `tools/mac_sync_engine.sh` (hard reset → reapply → rebuild → stamp
`third_party/smb-opt/.built-from`) and a guard in `tools/mac_run.sh` that **refuses to run the
engine** (exit 3) when the patch sha256 does not match the stamp. Two traps found while
testing it: `set -e` plus `$(awk ...)` on a missing stamp killed the script before it could
warn, and `git clean` skips patch-added files if they were ever `git add -N`'d, so the reset
must be `--hard`.

**Still open.** Expand throughput on the Mac is **unmeasured** — the control gate is too small
to time, so F106's proxy (~2.8x/thread) is all we have. That is P0.11b.

**Next.** P0.11b (throughput), then start using the Mac for difftest/ladder fan-out per
PROCESS "Parallel work on the second host".

## 2026-08-23 — Session 11 (cont.): S2′ = 184 (chain-safe boundary, F113); S3′ running; first Mac fan-out post-mortem
**Did.** The S3-from-x-755 dead end diagnosed (airborne S2 arrival → col-50 wall; the greedy-boundary trap, in the
experiment file) → S2′ with the boundary at x ≥ 800 ∧ Y ≤ 112: **first rung d184 GOAL at layer 184, proof-grade —
184 = the movement bound again** (F113). Goal print still truncated (the widened print slices an already-short rec,
`main.rs:987`; proper fix queued) — recovery-by-prefix from `layer_183.bin` worked again (10 matches). `chain_s2p.bin`
(6,917) **core-verified 333/333, 2 stomps in stride**; arrival is the designed chain-safe one (lands x ≈ 865, full
speed, 47 px before the pit lip). **Chain: root → x ≥ 800 = 333; enemies still 0 frames over the bound.** S3′
(x ≥ 1005 ∧ Y ≤ 112, the pit) probed at **82** and its ladder is running. First Mac fan-out ran end-to-end (sync →
gate → rung) but the d186/d188 insurance rungs were economically wrong (slack-2 rungs are 10⁷-scale by the frontier
law; 41M records by layer 27, killed) and exposed real setup gaps — all ten items in the P0.11d loose end (STATUS),
incl. a silently-dying macOS watchdog and the first real throughput datum (~0.84×/thread in-container, not the 2.8×
proxy). Merged the Mac agent's P0.11a push mid-session (F111 = Mac operational; my S2 fact renumbered F112).
**Learned.** Chain boundaries must force a grounded-or-landing arrival — and checking the arrival *state* against
the geometry before chaining beats finding out from the next segment's dead rungs. Cross-box ladder parallelism
only makes sense above the cheap end; the ladder is sequential by nature.
**Next.** S3′ verdict → S4 (the pipe; the F100 plant is the open cost question) → full-chain `replay_check`, slack
accounting vs 577, the staged-bound plan. Then the P0.11d doc fold-in, engine truncation fix, run 4 resume.

## 2026-08-23 — Session 11 (cont. 2): S3′ = 82, the pit is free (F114); S4 — the decisive segment — is running
**Did.** S3′ (x ≥ 1005 ∧ Y ≤ 112, the lift pit): probe 82, **first rung d82 GOAL at layer 82 — the movement bound
again** (45.5M goal transitions, 887.7 s); goal-parent prefix recovery had exactly 1 match (the koopa is live in the
ext); the path is a full-power 23-frame jump over the pit, **no lift ride**. `chain_s3p.bin` (6,999) core-verified
415/415, still exactly 2 stomps. **Chain: root → x ≥ 1005 = 149 + 184 + 82 = 415 — three segments, all exactly at
the y-coupled movement bound; nothing has cost a frame yet** (F114). S4 probed from the arrival: x-only root bound
**137** → the chain floor is 552, under the 554 double-framerule line — and the bound is blind to pipe B's climb
and every plant, so S4's ladder (d137 → 187, running) now measures precisely what the clock-gated obstacles cost.
User priority recorded: S4 outranks resuming run 4 for the local threads; run 4 resumes after S4 or at bedtime.
**Learned.** All three skill-gated sections were free for an exhaustive search — the H36 question has collapsed onto
the clock-gated mechanisms in S4 (the F100 wrong-warp-pipe plant above all: 47 up / 64 idle / 47 down, phase fixed by
arrival time). Goal-boundary hygiene: check the arrival state against the map before chaining (S2′/S3′ both passed).
**Next.** S4 verdict → chain_s4.bin, core-verify, **the chain total vs 575/577** (the headline) → full replay_check,
slack accounting, the seam-merge question if the number lands just above a framerule boundary; then the P0.11d
fold-in, the goal-print engine fix, run 4 resume.

## 2026-08-23 — Session 11 (cont. 3): S4 needs the big-run treatment — dedicated d112 on the Mac overnight; run 4 resumed
**Did.** S4 (case pipe-entry goal, x-only bound 137): the slack-0 rung blew the ladder's 20M cap at layer 62
(x ≈ 1161, dead 0) — F95's y-variety explosion; split into **S4a** (x ≥ 1284 ∧ Y ≤ 112, y-gated, root bound 112)
+ **S4b** (the ~64-px pipe-entry stub). S4a's own slack-0 rung then blew 20M at **layer 30** (x ≈ 1081, growing
30 %/layer): the y-term is dormant until ~25 frames from its goal, so this segment's middle is effectively x-only
over the climb approach — the ladder cap is simply too small here, as it would have been for S1's d149. Since the
rung was *growing* (feasible-looking), d112 got the d149 pattern **on the Mac** (506 G disk): `s4a_big_launch.sh`,
`mac_run.sh -m 8g`, 10 threads, `watchdog.sh` 120M/80G + a local 5-min ssh poll as backstop (P0.11d #8). First
launch was mine to own: I dropped the `--goal-x/--goal-y` flags — the case bound (137) > deadline → dead at layer 1
in 2.6 s; the backstop watcher caught it inside a minute, relaunched correctly (root Some(112) = deadline, search
pid 30712, watchdog 30713 both verified alive). **Run 4 RESUMED ~19:50** (`kill -CONT 172117`) — the local box is
free while the Mac grinds, per the user's priority (S4 outranks run 4, but S4's decisive run no longer needs this
box tonight). Local d137/d112 layer remnants deleted (19G + partial).
**Learned.** The ladder's 20M economy assumes the y-term covers most of the segment; when the goal sits > ~25
frames past high-variety terrain, budget for the d149 pattern up front. And a launcher written in a hurry loses
flags — the root-bound line (`at root: Some(N) (deadline D)`) is the launch check: N must equal D's plan, read it
before walking away. The backstop watcher earned its place in P0.11d.
**Next.** The Mac's d112 verdict (hours): GOAL → prefix-recover + `bfscx-path` ON the Mac, scp the path, chain →
`chain_s4a.bin`, core-verify, S4b probe/ladder (the plant tax read-out) → **the chain total vs 575/577**. "No live
states" → d114, same treatment. Then the P0.11d fold-in, the goal-print fix, the slack accounting.

## 2026-08-23 — Session 11 (cont. 3): the search explainer page (`docs/web/`)

**Did.** Wrote a human-facing explainer of Track A at the user's request — "explain like I'm 15, interactive,
about the *searching*, not the glitch/memory tracks". Twelve chapters built only from `docs/facts.md`,
`docs/experiments/` and `runs/` logs: the input explosion (16/frame) against the measured dedup'd layer sizes
from P2.1a; the 21-frame framerule with the real slack/deficit table and why the objective is a deadline rather
than a minimisation; the engine as a *model* (2,048 B of RAM vs a 12,792 B savestate vs our 96 B record) and what
the 3,836-line patch added (physics corrections F56/F70/F71/F72/F101, block states, the lift, `w42enemies.rs`,
layered BFS over all 16 inputs, ygate, position goals); the verification chapter the user specifically asked for
(difftest F102, the dump oracle F99 *with* its negative controls 119/20/63, bound audits, the byte-identical
regression control, core replay of every path); why BFS is forced (unit edge cost) and per-layer vs global dedup;
`g + h > D` and the x-table; the frontier law as an interactive slack dial (anchored on the slack 0/2/15/28
measurements) and the tight-first ladder with the deadline = bound proof argument; the ygate and the S1 collapse;
segments and seams incl. the S3 chain-unsafe-arrival post-mortem and the 45M-arrivals-pick-one framing; the
external-memory engine; the current 149/184/82/415 scoreboard with the two surprises (enemies free, pit free) and
the two negative results (1-1 pole, F88's 3 frames); and an honest limits chapter.
Interactive: the explosion counter, the framerule ruler, the slack/frontier chart, and an SVG block map of the
4-2 main area drawn from F92's exact geometry with the top route and the WR's bottom route (incl. the F80/F93
wall walk) toggleable.

**Built.** `docs/web/proving-mario-optimal.body.html` (source of truth, artifact form — no doctype/head/body,
the Artifact host injects those), `tools/build_page.sh` (splits at `<div class="shell">` and wraps into a
standalone document), generated `docs/web/index.html` (single self-contained file, hostable anywhere; only
external request is the Google Fonts stylesheet, every face has a fallback stack), and `docs/web/README.md`.

**Learned / noted.** The page is a second consumer of the facts ledger, so it is now a maintenance surface:
the scoreboard and the results table hardcode 149/184/82/415 and will be stale the moment S4 lands. Recorded
as a STATUS loose end with the artifact URL (republishing without the URL creates a *second* artifact).

**Next.** Unchanged: S4 verdict → chain_s4.bin → core-verify → the chain total vs 575/577.

## 2026-08-24 — Session 11 (overnight): five segments at the bound; the coupled passage stops the chain at 465
**Did.** S4a-i′ (x ≥ 1130 ∧ Y ≤ 176 re-gate) = **50 exactly — the fifth consecutive segment at its movement bound**
(chain `chain_s4aip.bin` = **465**, core-verified 465/465, still 2 stomps). Then every cut of the remaining
pit-arc → pipe-A → bricks passage failed: the over-flier arc is fated to the floor (misses the cap by ~7 px), no
grounded gate-point exists inside the passage, the descending-lander root prices the bricks at > 60 empirically
(ladders d36–d62; d62 blew 20M) vs a record budget of ≤ 52. Full reasoning + numbers in the experiment file
§"The coupled passage". Auto-picks found the sky twice more (`Y ≤ GY` never fences it) → hand-picking is standard
at every seam; the dual-rank pick found NO grounded and NO rising max-speed states at 1130 (all mid-descent of
S3′'s arc) — the coupling reaches back to S3′'s boundary. Housekeeping: dead-run layers cleaned everywhere
(~250 G reclaimed), the live 1130-seam layers retained on the Mac, run 4 resumed 01:30 (verdict ~10–11am, precise
watcher armed after a "grabs 0" false-match), Mac caffeinated, everything committed stepwise.
**Learned.** A segment chain's gates must sit on standable ground OUTSIDE coupled aerial maneuvers; where no such
ground exists, the maneuver is one search — and this one (bound ~118 from prefix 333) is beyond both local boxes.
The night's method upgrades: y-term range = the segmentation ruler; probes over hand physics; hand-pick every seam;
verify sed matched; retention until the next segment chains.
**Next.** Morning: run 4's H28 verdict; the coupled-segment decision (cloud auction box vs bound engineering vs
H34 unlock); the wrap-up unit (P0.11d, goal-print fix, slot forensics, sweep list). The chain's 465 verified frames
and five exact segment optima stand regardless of the route chosen.

## 2026-08-24 — Session 11 (close): run 4 reports — H28 refuted, 1-1 closed (F116)
**Did.** Run 4's first grabs came at layer 234 (33.3M, all F55's slow band); the process OOM-died expanding 235 and
the whole-file resumes died the same way 3×. Recovered the table with `--stop-step 234`, then searched layers 235–238
by slicing layer 234 into 8 disjoint parts and resuming each (sound for grab existence; ~25 min total): **no FPG grab
exists ≤ step 238 — H28 refuted proof-grade in the over-approximating model; 1-1 is closed** (F116; H29 parked).
Corrected the morning's premature "candidate" reading in the docs. The 4-2 plan (floor-clip ladder → beam mode →
dominance/y-term → cloud for optimality) is recorded in STATUS and the experiment file.
**Learned.** Read the engine's output columns before celebrating (fpg true/false is the whole question); unbounded
bookkeeping is the OOM you never budgeted for; partitioning a layer's parents is a code-free, sound way past it.
**Next.** The 4-2 plan step (i): the floor-clip ladder from the 465 chain (bound 62); step (ii) beam mode. Wrap-up
unit: P0.11d, the goal-print fix, WR slot forensics, the sweep list. Loose end: delete `runs/P2.1b-model/room_layers`
(71 G) + the slices once F116's write-up is reviewed.

## 2026-08-24 — Session 12: the ledge was the fault; the G-chain runs the pipes at the bound; the plant guards the finale
**Did.** Plan step (i) (the floor-clip ladder from 465, Mac, d62–d82): no path at any rung, 36 s total — every
465-rooted continuation slams pipe A's face (F117); H37 untested (pipe B never reached). Diagnosis by trace: the
S3′ arrival (Y 45 at x 1005) is FORCED onto the vine ledge at step 418, and the session-11 chain-safety note
("passes under at Y ≈ 65") was hand physics, wrong. The WR passes UNDER the ledge and runs 1005 → 1284 at exactly
the movement bound. Fix: S3′ rerun (deterministic to the digit), hand-picked an under-ledge arrival with the new
`tools/pick_parent.py` (census tool, full 96-byte records), then chained the WR's own standable gates: **G1 floor
1090 = 34 = bound (grounded re-pick; the auto-pick was a fated mid-jump), G2 pipe-A cap 1177 = 35 = bound, G3
pipe-B top 1239 = 25 = bound — chain 509, core-verified at every stage (0 mismatches, 2 stomps), = the WR's
step-540 player state 31 frames early.** G4 (pipe entry, floor 44 → total 553): d44–47 refused — our bump-free
world spawns a piranha plant IN the wrong-warp pipe (risen, static to ~step 566; 34.2M deaths at layer 46;
standing in the entry window = contact). HappyLee's (64,3) vine bump was slot management: bump → slot-5 vine →
the enemy loader injects an inert VineObject into the first free normal slot → no plant at the col-84 render.
The full mechanism read from the disassembly and documented; 77,696 vine-capable rising S3′ arrivals exist at
the bound in the retained layer_081.bin (`h34_riser_record.txt`). **H34 unparked by the plan's own trigger.**
Tools: `pick_parent.py` (new), `replay_check.py --enemies` (+ a latent 4-tuple unpack fix, regression-checked),
`bfscx_ladder.sh` third rung ending ("no goal at the deadline" no longer aborts the ladder).
**Learned.** Probes over hand physics, again — twice (the ledge note; the "misses the cap by 7 px" story).
The truncated-goal-print bug reproduced locally (recover the full record from the last layer by prefix;
main.rs:987 audit still queued). First-arrival gates on standable ground + census-picked landing/grounded
parents made four consecutive seams work without a single re-gate. And the biggest: HappyLee's "irrelevant"
bumps are load-bearing slot management — routes here are enemy-slot programs, not just movement.
**Next.** P2.5c-3: model the vine (design written), unlock (64,3) in the search, oracle to 0 on WR rows
7038–7172, then the G-line re-search from a vine-capable arrival → G4′ with an empty pipe → the total vs 575/554
→ assembly + two-emulator verification if ≤ 575.

## 2026-08-24 — Session 12 (cont.): the vine unlock → 4-2 main area in 553, two framerules under the record
**Did.** Modeled the vine (design → implementation → validation in one sitting): `CLASS_VINE`, the flag in spare
ext bits, the loader injection on the frenzy paths, KillVine; oracle **0 mismatching rows over 586** (was
"everything after 7038"), wrong-warp plants 0, tunnel difftest 60/60 clean with the former bump-stoppers now
core-compared through the bump; bump-free behavior byte-identical (S3′ rerun reproduced to the digit on the new
binary). Then the G-line from a vine-capable arrival — four wrong chains taught four physics facts (the [72,78)
bump band / the side-slam, continuous-A low gravity, the v_force index alias, the RunningTimer ground clamp; all
in F119) — and the fifth chain ran the table: **G1v 34, G2v 35, G3v 25, G4v 44, every one = its movement bound;
main area 553 = 149+184+82+34+35+25+44; core-verified entry at record 7136 (GES 3, Down, 0 mismatches, 2 stomps)**
— F118. The wrong-warp pipe is bare in every bound-time line (the bump is forced at the bound); plant C spawns
into the freed vine slot exactly as in the WR's world.
**Learned.** The census-pick discipline needs the PHYSICS fields, not just position: v_force (with its encoder
alias), RunningTimer, the goal-transition input (A|R / B|R). The seam protocol's "probe, don't hand-derive"
paid five times today. And the deepest one: HappyLee's 2011 route encodes all of this — the apex graze IS the
only legal bump, his vine IS the plant suppressor; the search rediscovered his moves from mechanics alone, then
went two framerules further.
**Next.** (1) Two-emulator verification + movie assembly (WR prefix + our 553 + the post-entry splice; the
warp-zone framerule alignment analysis — what 553 does to the full-run time). (2) The optimality note (552 vs
553: at most one frame open, worthless for framerules — 533 would be needed for a third). (3) The parked
alternates (brick-landing line, over-flier G3) are moot at the bound. (4) The fork decision (Needs user input).

## 2026-08-24 — Session 12 (afternoon): verification catches the warp, the scroll ledger, the drift campaign
**Did.** Emulator round 1 (new `tools/splice_fm2.py` → `w42_553.fm2`/`.bk2`): FCEUX frame-perfect on the main
area (552/552 = the model, entry Δ = 35 rows vs the WR) — and the wrong warp DIVERGED (ours re-enters at page 8
x 2072, falling; the WR at page 0 x 24). Root cause chain, fully closed: F40 (on the books since session 6) —
the warp needs the page-5-col-15 area-change command unparsed; our parser consumed it (cursor 18 vs the WR's 15)
because our entry's ScreenLeft was 1237 vs 1216. Both conditions now REFUSED in the hook (eoff ≥ 16, sl16 ≥
1217; engine + patch committed, Mac resynced + gate-checked — en route: mac_run.sh got the P0.11d-#4 PATH shim,
and mac_sync_engine.sh must run ON the Mac, whose repo needed the `laptop` remote added). Then the scroll
ledger (F120): the offset Mario-x − ScreenLeft is a LATCH; collision-push displacement is the only minting
mechanism; the WR mints +21 px INSIDE the col-30 wall — the wall walk is passage + vine + warp key. The drift
geometry: the goal-pipe face sits 1.06 px beyond the relative-112 wall — the mint stages at the bricks' face
(+11) then the pipe face (+17); the G4a/G4b split (chain 539) dead-ended on exactly that (the gate cut the
staging) and was retired. **Campaign running: dedicated rungs from 509 — local d58, Mac d62 — vs the d ≤ 66
budget** (see STATUS Running jobs for the full decision tree and the pivot if dry).
**Learned.** The two-emulator rule earned its keep on its first real test: the model was exact, the GOAL was
underspecified. Case goals must pin every load-bearing state byte (the scroll and the parser cursor were both
in the state all along). And the session's through-line: HappyLee's 2011 route is a machine — bumps are slot
management, the wall walk mints the warp key, the apex graze is the only legal vine touch; each "quirk" we
removed came back as a requirement.
**Next.** The rung verdicts → the decision tree in STATUS (record-verify path or d64/d66 or the bottom-route
pivot). Then: BizHawk re-run, the full-movie assembly + framerule math, the optimality note (552/553), the
fork decision (Needs user input), P0.11d fold-in.

## 2026-08-24 — Session 13: the rungs blew up on a blind bound; the scroll-aware drift bound is the fix
**Did.** Read the two drift-campaign rung verdicts: both WATCHDOG-KILLED at layer 37 (local d58 126M > 120M; Mac
d62 248M > 200M, its container ran on to layer 38 = 329M until I `docker kill`ed it — a Mac-watchdog loose end:
it killed only the docker client). Both pinned at `max x 0x530f0` = 1328.94 = the F40 refusal wall, `goals 0` —
**memory blowups, not "no path."** Diagnosed the cause: `W42Main`'s `--enemies` case bound was the x-only x-table
to X 1348, blind to the F120 scroll latch, so every wall-pinned state (millions, differing only in Y / blocks /
enemy ext) looked ~2 frames from the goal and survived to the deadline. Built the fix — `heuristics::drift::DriftBound`
(new engine file): a sound lower bound from a relaxed BFS over (X, Player_Y, scroll offset m, side-collision credit)
with the exact scroll regimes + collision pushes at BB42 sites, distance to X ≥ 1348 inside the `X ≤ 1328+m` wall.
Case bound → `max(x table, drift)`, ON under `--enemies`, `--no-drift` disables; also refused the goal transition
itself when its own frame scrolled `sl16 ≥ 1217` (`goal_refused`). Validated: control gate byte-identical (drift
off); the WR's real warp survives `--check-path` with 0 violations and reaches the goal (drift on) while 32,472
wrong-scroll entries are pruned; `tools/drift_audit.py` — 400 trajectories + WR, 211,675 consistency pairs, 0
violations, minting exercised to rel 132, h up to 67 in the wall band. Patch regenerated (26 files incl. drift.rs),
verified applying cleanly to the pinned commit. Launched the decisive local d58 rung with the bound, resumed from
the pre-drift layer 37.
**Learned.** A watchdog kill is a null result, never a "no" — the campaign's decision tree only advances on a real
goal-or-exhaustion verdict, and the frontier explosion was our own heuristic wasting effort on states the scroll
rule already rules out. The x-only bound had been carrying every segment (S1–S4) because those were open terrain;
the wrong-warp finale is the first place the missing scroll term actually bites. F121; write-up in
`docs/experiments/P2.3c-2c-main-area.md` §P2.3c-5.
**Next.** Read the d58-drift verdict (layer 38 = the with/without datapoint). GOAL at d ≤ 66 → the record pipeline
(path → core → splice → FCEUX warp-dest check → BizHawk); dry through d66 → pivot to the bottom route. Resync the
Mac to the drift patch and run d62/d66 in parallel. Then the P0.11d Mac-watchdog `docker kill` fix.

## 2026-08-24 — Session 13 (cont.): the drift bound settles d58 (dry), but d62–d66 are a resource wall
**Did.** Ran the drift-bounded ladder. **d58 = proof-grade DRY** (local, resumed from the pre-drift superset;
frontier collapsed 130M→0 by layer 48, `no goal within 58`, max x pinned at the relative-112 wall throughout —
no path mints enough offset in ≤ 58 steps). **d62 (Mac, from scratch) and d66 (local) were CAP-KILLED, not
verdicts:** the drift term only prunes once `D − L ≤ drift_h` (~20), so a looser deadline delays the collapse and
the wall frontier accumulates for the extra layers — d62 hit 329M at layer 38 still growing ×1.35 (collapse 4
layers off ⇒ ~1B peak), d66 hit 143M at layer 30 growing ×1.2 (multi-billion). So d62–d66 are ~10⁹-state searches,
beyond the laptop's 147G / the Mac's ~130G free. Stopped both, cleaned the local box. **The Mac's P0.11d watchdog
bug bit again** — the watchdog killed only the docker-run client, the orphan container ran to layer 41 filling disk;
`docker kill`ed it.
**Learned.** The drift bound is *necessary* (it makes the finale finite and decidable, and settled d58) but not
*sufficient* on this hardware for loose deadlines — the peak scales with the deadline, not just the answer. The
wall frontier's likely dominant multiplier is the 64-byte enemy ext; the vine-bumped chain suppresses the plant, so
an enemy-ext abstraction (if no live enemy touches the finale) may bring d62–d66 back under the laptop's disk — the
cheapest thing to try before cloud.
**Next (fork — STATUS "Needs user input").** (1) cloud for d62–d66; (2) enemy-ext frontier abstraction (unblocked,
try first); (3) bottom-route pivot (F79+F88 → 575, non-cloud, no mint search). d58 dry + HappyLee's 2-short + the
peak analysis all suggest the top-route mint is marginal, but it is NOT refuted (d62–d66 unsearched; "too big for
this hardware" is not a proof). Also queued: the P0.11d Mac-watchdog `docker kill` fix.

## 2026-08-24 — Session 14: STATUS.md cleanup (branch `status-cleanup`)
**Did.** STATUS.md had become a ~100 KB session-by-session narrative (single lines of 10+ KB; "Running
jobs" carried six paragraphs of finished history; "Next up" listed units done days ago). Rewrote it as a
status: a "Where we are" block, Running jobs (none — verified `pgrep` empty, Mac `docker ps` empty),
an empty In progress, a refreshed Next-up table (done units removed; P2.3c-6 = the cloud finale and
P2.3e = the next framerule level now carry the fork), one line per Done unit, current loose ends (the
Mac's 400 G of stale layer dirs and the local 81 G `runs/P2.1b-model` surfaced with sizes), the fork and
the other user decisions condensed, Key numbers trimmed to the current headline numbers, and the
Model-omissions table updated (bounces admitted, vine modeled, scroll latch, RNG row). 100 KB → 28 KB.
Nothing was deleted: the old file is archived verbatim at `docs/archive/STATUS-2026-08-24-pre-cleanup.md`;
material that lived ONLY in STATUS got real homes — `docs/search-runbook.md` (new: capped-run rule,
ladder/dedicated-run pattern, the seam protocol, the record pipeline with the FCEUX warp-destination
check, patch discipline, cleanup) and `docs/experiments/P0.11-two-box.md` §7 (the P0.11d Mac fan-out
lessons, now 13 items incl. the docker-kill bug and the intent-add patch rule).
**Learned.** STATUS hoarded runbook content because there was no runbook file; PROCESS §"Parallel work"
still points at STATUS "Running jobs" for the cgroup rule, so that one-liner stays there too.
**Next.** User: review the branch and merge; answer the fork (A cloud / B pivot, default B); clear the
Mac's stale layer dirs. Then the loop resumes from the new Next-up table (P2.3e unless (A)).

## 2026-08-24 — Session 14: the 4-2 top-route warp is closed — the offset can't be minted (F122)
**Did.** User steer: no cloud (CPU cap), don't pivot levels, **loosen the optimality requirement** to *find* a
≤575 top-route warp rather than *prove* the finale optimal (and keep optimal runnable). Built `bfscx --beam N
[--beam-offset] [--log-offset]` (opt-in per-layer beam; **optimal mode byte-identical with beam off** — control
gate `6 16 34 70 134 673 3472 16472 69489 257001`). Re-verified the warp requirement from ground truth: WR enters
at ScreenLeft exactly 1216 / offset 132 (dump row 7173); parse threshold asm-exact at SL ≥ 1217 (`CheckRightBounds`,
checked against the $2F command's own parse); mint physics = collision-push welded to speed-zero in
`impede_player_move` (no fast-mint hole); the drift bound's C=16 credit over-credits re-accel → d58 dry is sound.
Then ran the finder: h-first & offset-first beams from 509 (d72) and 484 (d100), plus two no-beam exhaustive probes
(drift from step 530; position-goal 484→x1284, 23 layers exhaustive) — **the scroll offset is frozen at 112 in
every one; nothing mints.** Mechanism: minting is the bottom route's col-30 floor wall walk; the top route's walls
are top surfaces / jumped-over, and F117 blocks floor access past pipe A. **F122: strong evidence (not formal
proof) the top-route wrong warp is structurally infeasible — not "2 frames short."** Retires the P2.3c-5 cloud fork.
**Learned.** The drift bound (admissible → assumes minting available) is sound for *proving* but too optimistic to
*steer* a beam (it read wall-pinned states as ~20 frames from the goal); h-first and offset-first beams both prune
the mint-setup (delayed-payoff maneuver) — but here it didn't matter, minting isn't generated at all. Ops: layer
dirs MUST go on the NVMe, not the tmpfs scratchpad (a run filling `/tmp` OOM-died AND starved the shell of fork
memory). The STATUS cleanup commit (`eb597f6`) landed mid-session from another terminal — consolidated on main.
**Next (user question, not chosen).** 8-3 (deficit ~7) with the tooling, the 4-2 warp zone (H35), or another lead.
Beam tooling is reusable. `docs/experiments/P2.3c-2c-main-area.md` §P2.3c-6; F122; H36 updated.

## 2026-08-24 — Session 14 (cont.): the mint economics close 4-2's bottom route too (F123); Mac reclaims 401G
**Did.** User asked whether a cheaper/earlier mint could save the wrong warp. Built `bfscx --goal-offset N` and
measured the mint directly from the WR's col-30 arrival: min 132-mint = **27 frames** (vs the WR's ~34) — but the
trace comparison exposed the trap: the WR mints by **sprinting inside the sct-frozen scroll window** (impede arms 15
frames of frozen scroll; foot impedes refresh it) so it finishes its mint *with 15 units of speed built*, while every
min-frame minted state sits at ~0 speed. Continuation probe from the chained 27-frame mint: case bound 357 → **total
≥ 584 > 575**. With F94's tightness and the ~0.65 px/f rate law: bottom-route floor ≈ 584–585, deficit ~9–10 —
matches the framerule accounting from the other side. **4-2 is now closed for a framerule on both routes with
mechanisms** (F122 top: no mint possible; F123 bottom: the mint is speed-priced at ~30 frames). H38 (speed-preserving
mint) records the residual. Inconclusive runs recorded as such: the full-level offset-first beam lost the WR's own
line (the user predicted the beam-ordering bias); the Mac's root-190 beam was walled by the H34 item-bump refusal at
col-28 (lesson: root ≥ 200). Mac: resynced to d679bb8, gate exact, **401 GB stale layers reclaimed (133→533 GiB)**.
**Learned.** "Earliest goal" ≠ "best goal" when the goal is a resource (offset) bought with a resource (speed) — the
right comparison is full-state dominance, and the continuation probe is the cheap way to price it. And the level's
deep structure: 588 = 553 movement + ~31 warp-key + ~4 slack, conserved across routes — HappyLee's route was already
sitting on the conserved price.
**Next.** The pivot the user picked before the mint question: 8-3 (deficit ~7 after F37's FPG) / 1-2 (~5 on the
best-known route) with the existing tooling — new cases in the engine. 4-2 rests unless H38's enumeration gets picked up.

## 2026-08-24 — Session 14 (close): P2.3c-7 — the vine-snap mint refuted in the asm; 4-2 rests; pivot queue set
**Did.** Launched the vine unit with agreed kill criteria; the disassembly read killed it in step 1, twice over:
(1) every grab of the 4-2 vine is an irreversible autoclimb warp commitment (side-point-only grabs × rows-≤2 cells
⇒ Y < 32 ⇒ GES 1 ⇒ forced-Up JoypadOverride ⇒ area change to $2F — the vine IS the legit warp-zone route, the wrong
warp its shortcut); (2) even a leave-able grab nets ≤ +14 px at wall-mint rates ⇒ ~578–581 > 575. Completed H38's
x-writer enumeration (flagpole/platforms/enemies/springs/clamp all ✗) ⇒ H38 refuted for 4-2, code-level. Unit
closed same-session per the no-third-push agreement. User asked about beaming 1-1: room 3 is proof-closed (F116),
but the real door is H29 (room 1, bounce-assisted, never searched) — exhaustively searchable at deadline 367
(~5M/layer, F82), needs only the enemy-module port (classes already in w42enemies.rs). Queue: H29 → 1-2 → 8-3.
**Learned.** Read the code before building the harness — the half-day difftest plan was preempted by 30 minutes of
asm. And the project's recurring shape held once more: 4-2's every "trick" (bumps, wall walk, vine) is load-bearing
machinery for the warp, not optional style.
**Next.** P2.5b-1: port the room-1 enemy rules into the engine (adapt w42enemies), difftest to 0, then the
deadline-367 exhaustive room-1 search — the H29 verdict and the cheapest framerule on the route.

## 2026-08-24 — Session 14 (night): 1-1 port lands + closes H29's rungs; the 8-4 campaign opens and finds its real shape
**Did.** (1) P2.5b-1: the room-1 enemy port validated to the F102 standard (WR 368/368; 500 trials / 82k frames /
0 diffs) — **d367 DRY (exhaustive, extinct at layer 21) + the WR reference line 0 bound violations with the goal
at 368** ⇒ H29 refuted modulo the d368 in-frontier control (still running, watchdog armed). (2) The 8-4 campaign
(user decision: primary track): P2.2a forensics — **the room-3 wrong warp parses at SL ≥ 3345 and the WR hits it
with ZERO pixels of margin** (hand-tuned brake, rel pinned 112); `W84Room3` case built (Small+scroll, the warp
condition in the goal, F89 overshoot bound), **WR line 195/195 exact on the core** — then the random battery
did its job: 9/100 trials diverge, traced to a **flying-cheep-cheep stomp** — room 3 is 3 piranha plants (one IN
the warp pipe; F100's distance rule is how the WR enters) + a continuous LFSR-driven cheep frenzy. The
premature d194 (slack-29, bound horizon bug — fixed to 96) was killed; the search waits on the enemy layer.
**Learned.** The difftest discipline earned its keep twice in one night (the w11 port passed it; the w84 spec
failed it exactly where it should). pkill self-match bit again (memory rule stands). And the recurring theme
at its purest: HappyLee's lines thread zero-margin scroll thresholds THROUGH enemy rain — every level's record
is a scroll+slot program, and our edge is that we can now read and search those programs.
**Next.** P2.2a step 3: port the plant class into a w84 enemy module + model the cheep frenzy (asm anchors in
the experiment file), difftest to 0, then the d194 rung with `--enemies`. d368's verdict closes 1-1 when it lands.

## 2026-08-24 — session 15 (P2.5b-1: H29 refuted, 1-1 closed end to end)

**Did.** Picked up the one running job, the `w11_d368 --check-path 368` positive control, and killed
it — after measuring it. At layer 90 of 368 it held 94 GB of layers, a 61.3M-state frontier growing
×1.10/layer, with 105 GB of headroom to the watchdog floor: ~10 more layers, and ≈1.6 TB / ≥12 h to
finish even if growth flattened. Not a laptop run. Then found that it had **already produced the
control I needed, 43 minutes earlier**: `--check-path N` audits the reference path *before* layer 1
(main.rs:938–950) — it replays the WR's own inputs, evaluates the goal test, and checks the bound
against the path. Its verdict was sitting at the top of the log: WR line → `StateChangeVerticalPipe(57,7)`
**GOAL at step 368**, `0 bound violations over 368 steps`, two `object event Stomp` on the way.
Deleted the dead layer dir (94 GB back).

**Learned.**
- **H29 is refuted, proof-grade — 1-1 room 1 is optimal at 368 with the enemies in the model (F124).**
  The d367 rung was dry in **4.7 seconds**. The whole verdict rests on the bound being admissible under
  `--enemies`, and that closes at code level, not by audit: (1) pipe entry needs the **right** foot on
  `cv 0x11` (emu.rs:485) and `BLOCK_BUFFER_X_ADDER_DATA[0x10] = 0x0c00` makes that `x_pos ≥ 0x39400`,
  which is *exactly* the case bound's target — the bound can't ask for more x than the goal does;
  (2) `src/w11enemies.rs` contains no reference to `x_pos` or `x_spd` at all, its only player write being
  line 315's stomp bounce `s.y_spd = -4<<8`. A bounce moves y. The x machine the table is computed over
  is the one the enemy-aware search steps. That is the argument H29 always needed, and it is three greps long.
- **With H28 (F116), H21 closes too: 1-1 cannot deliver its missing frame on any modeled route.**
- **Where 1-1's frame goes.** `k + h` along the WR's line is 367 for steps 1–20 and **368 from step 21
  onward, forever** — one transition. Step 21 is an airborne frame of the opening jump that buys no
  progress in the x table's terms; Mario lands at 22 with x_spd frozen at 0x18f0. The d367 dry proves the
  loss is *forced*: every reachable state has spent it by step 21. After that the WR rides the bound
  exactly for 347 steps and enters the pipe at x 0x39410 — **0x10 past the threshold**, the earliest
  admitting pixel. HappyLee's 1-1 is not merely optimal, it is tight against the bound the whole way.
- **Sizing lesson, worth carrying to 8-4.** "Deadline = optimum + 1" is not a cheap control. Zero slack
  gave 36 states; one frame of slack gave 61M and climbing, because `h` is a coarse x-only bound and
  tens of millions of states can sit one frame behind the optimistic line. F82's "~5M states/layer at 1
  frame slack" was optimistic by an order of magnitude. Before paying for an exhaustive `--check-path`
  rung, read the reference-path audit it prints at startup — that is usually the control you actually wanted.
  This applies directly to the queued **d195 check-path control** in P2.2a: expect the same blowup, and
  plan to take the verdict from the startup audit plus the d194 dry.

**Next.** P2.2a, the 8-4 turnaround room (H25) — the campaign opener, already In progress with its
forensics checkpoint (WR margin over SL 3345 = ZERO px, `W84Room3` built, WR line 195/195 exact). Its
step is the `w84enemies` port: the piranha-plant class from `w42enemies` plus the flying-cheep frenzy
(`FlyCheepCheepFrenzy`/`InitFlyingCheepCheep`/`MoveFlyingCheepCheep`), difftest to 0 differences
including cheep stomps, then the d194 rung with `--enemies`.

### Session 15 continued — P2.2a: the 8-4 room cut at the apex

**Did.** Took the queued unit (port the plants + cheep frenzy into `w84enemies`) and deliberately did
not write it. Two cheaper things came first, and both changed the plan.

Cut the 195-frame room at the WR's **apex** — max x 3457, the frame its speed crosses zero, prefix 162
— and the tail becomes a 33-frame segment inside the runbook's ruler. It answers immediately:
`at root: Some(33)`, 0 bound violations, **96 goals at layer 33** (7.7 s); the d32 rung dies at layer 1.
**h(apex) = 33 and the WR spends exactly 33** — the return leg is on its bound with zero slack, so
**H25's frame is not in the turnaround**. It is in the approach, or in arriving at a different apex.

**Learned.**
- **A real hole in the case bound (F125).** `W84Room3`'s heuristic ended `} else { Some(0) }` — every
  state with SL ≥ 3345 and x ≤ PIPE_XMAX scored zero. Admissible, so no wrong answers, but it can
  never prune, and since Mario turns around only 53 px right of the pipe most of the frontier fell into
  that half-plane and became immortal. That is the `pruned 0` on every room-3 rung, going back to the
  first d194. The missing piece was the entry window's **left** rim, and it came from the same foot
  geometry that closed 1-1 this morning: left foot `cv 0x10` in col 212 ∧ right foot `cv 0x11` in col
  213 ⇒ x ∈ [0xd4400, 0xd4d00). Two rooms, two levels, one geometry — worth remembering that the
  entry-window arithmetic is reusable.
- **I got the deadline units wrong, and it cost 27 GB.** `max_steps` counts layers from the
  *post-prefix* root; I passed the WR's absolute 195 on a prefix-162 rung and handed the search 162
  frames of slack. It behaved exactly like the other blowups (`pruned 0`, 100M states by layer 23)
  and I briefly read that as the bound bug rather than my own arithmetic. The tell I should have
  trusted: `at root: Some(33) (deadline 195 steps)` — the two numbers printed side by side, and 195−33
  is the slack, in plain sight. Now a runbook rule.
- **The whole-room rung is not rescuable by horizon.** Root 183 vs deadline 194 = slack 11. The
  obvious suspect was the overshoot horizon (96 steps for a ~162-frame approach, everything beyond it
  extrapolated at max speed) — but horizon 200 leaves the root at **183 exactly**. So the 12-frame gap
  is terrain plus the y-coupling of pipe entry. F95's ruler holds for 8-4: the room gets searched in
  chained segments or not at all.
- **The cheep frenzy is state-coupled, and the checkpoint's premise was wrong (F126).**
  `InitFlyingCheepCheep` reads `Player_X_Speed` and `Player_X_Position` — cheeps spawn *relative to
  Mario* with speed chosen by a seed his own velocity perturbs. So the LFSR is frame-indexed but the
  spawn law is not: two trajectories differing in x or speed meet different cheep fields, and the ext
  multiplies the state space instead of riding along as a frame index. That is a much larger port than
  the goombas were, and it is now deferred behind a decidable rung. The right order is find-then-model:
  an enemy-free **goal** is a candidate you replay on the core, where the cheeps are checked for one
  path; only an enemy-free **dry** actually needs the model (enemy-free is neither an over- nor an
  under-approximation — no deaths is a superset, no stomp bounces is a subset).

**Next.** Segment the approach (root → apex, 162 frames): either a y-coupled/ygate-style bound for
`W84Room3`, or a further cut at the brake start (WR row 16492, x 3428, speed 40), then chain the pieces
with the seam protocol. `w84enemies` stays deferred until a rung needs it.

## 2026-08-24 — session 16: the beam was the bug

**Did.** P2.3c-8. The user argued that a beam ordered by one global key "essentially falls back to
the greedy search by segment, because we're getting rid of anything that you would pay for early to
gain back later." That is right, and it was load-bearing: `--beam N` (lowest-h) and `--beam-offset`
are per-layer first-arrival gates — the same lossy operation as a segment seam, applied every frame.
Recorded as H39, shipped the fix (`--beam-buckets off,y,spd,sub[,vf]`, `--beam-max`, plus
`smb-opt offset-census` because `pick_parent.py` cannot decode `left_screen_edge_pos`), regressed
beam-off to byte-identical, then re-ran the one verdict that rested on beams.

**Learned.**
- **F128 / H39 confirmed.** Under the same root, deadline and budget, a bucketed beam finds what a
  global one cannot. The specific casualty: F122.
- **F127 — F122 is refuted.** "The top route cannot mint scroll offset; the offset never leaves 112"
  was an artifact. The bucketed beam carries it **112 → 132** and reaches a **core-verified** pipe
  entry (87/87 frames, 0 mismatches, x 1348 / ScreenLeft 1216 / AreaPointer $2F — the WR's own entry
  condition). The minting maneuver is **19 frames of held Left**: motion away from the goal, deleted
  by h-first on frame 1. Also: two of F122's five table rows never measured the offset at all — the
  `--log-offset` print postdates them, so those entries were inferred from max-x.
- **F129 — but it warps to the wrong place, for a new reason.** The scroll keeps advancing during
  the pipe descent, crosses the 1217 threshold two frames in, and the destination flips $2F → $42.
  The WR's `Player_X_Scroll` is **0** at entry and stays 0 (offset pinned at 132); ours is 2 and the
  offset decays 132 → 107. The WR's mint is a *latch* (collision-push, F120); the sct-freeze mint the
  top route uses is *transient*. **The warp needs a second, unmodelled condition: zero integer-x
  advance on the entry frame.** So `goal_refused` is under-constrained and every wrong-warp GOAL the
  engine currently reports is suspect — including the 900 at layer 87.
- **Blast radius.** F123's bottom-route economics also came from a single-key beam, so "4-2 closed
  both ways" is caveated, not retracted — it needs a bucketed rerun. And the same defect lives in
  every first-arrival segment gate: P2.2a's planned approach-cut is provably incapable of finding
  H25's frame, because F125 already proved the WR's apex dead and the cut goals on that apex.

**Next.** P2.3c-9 (add the F129 condition to `goal_refused`, re-run the d90 rung) — nothing else in
the 4-2 line is trustworthy until the engine stops reporting non-warping goals. Then P2.3c-10
(re-audit beam-derived verdicts, F123 first) and P2.2a′ (multi-apex seam).

### 2026-08-24 — session 16 addendum: review notes folded in, threads enumerated

A second agent's review of the bucketing work was handed over. Verified it against the
disassembly rather than accepting it, and it holds up with one correction and one scope limit.

- **F130 (new, verified).** The 8-4 cheep frenzy's coupling to the player is far weaker than F126
  assumed. `InitFlyingCheepCheep` reads `Player_X_Speed` only as a **3-valued class** (zero /
  1..$18 / ≥$19 unsigned) for the speed-table row, and again as a **2-valued** gate on the
  direction flip. **Correction to the note:** `Player_X_Position`/`Player_PageLoc` are *not* key
  dimensions — the spawn is placed *relative* to Mario (`Enemy_X_Position = Player_X_Position ±
  FlyCCXPositionData[y]`), so the geometry is translation-invariant and absolute X never selects a
  branch. Also `$00` is overwritten by a third LFSR nybble whenever `PseudoRandomBitReg+1 & 3 != 0`,
  so the position index is usually pure LFSR. Net: the port is ≈3× a frame-indexed class, and
  F126's "bigger than budgeted" is directionally right but quantitatively far too pessimistic.
  This unblocks the 8-4 primary track (new unit P2.2a-port).
- **H40 (bucket keys from downstream branch variables).** Right for *exploitation*, with a scope
  limit that matters: a code-derived key presupposes knowing which routine matters. F122 is the
  counter-case — there was no known downstream routine, and it took *generic* diversity to find a
  mint nobody believed existed. Recorded as complementary, not competing: generic for discovery,
  code-derived for exploitation. Cost is a product of cardinalities, not 2^k, and `--beam-max`
  already bounds it.
- **H41 (framerule-flat objective).** Correct and sharp: below a rule boundary a saved frame is
  worth zero, so an h-ordered beam ranks on noise and pays at the seam. **Scope: not 8-4** — it is
  unquantized, so time genuinely is the objective there (H24). Applies to 4-2/1-1/1-2/8-3.
- **Two-stage discipline** (beam discovers, exact rung promotes) and the census/objective rules are
  now standing rules in `docs/search-runbook.md` §7 rather than living in one experiment file.
- **P2.3c-11** — the suggested free validation (re-run 4-2's seven seams bucketed, expect 553) is
  worth doing and cheap (the `s4*_layers` are retained), but its honest frame upside is ~1 by
  current accounting; its real value is proving the machinery sound before 8-4 depends on it.

**The number that frames everything:** 4-2 = 553 movement + key, and the 575 line allows a key of
22. Bottom route ~31; top route 43 as found today, on a path that does not yet warp correctly and
gets *more* expensive once F129's zero-scroll entry is enforced. Nobody has measured the cheapest
top-route mint. That is P2.3c-9 Part B.

### 2026-08-24 — session 16, part 3: the goal fix failed the control (and the control was broken too)

**Did.** Started P2.3c-9 Part A. Before implementing, measured what the scroll actually does through the
whole pipe descent instead of assuming — prompted by the user asking whether a high-but-decaying offset
could work, which is exactly the case a "require `Player_X_Scroll` = 0" rule would have over-constrained away.

**Learned (F131).**
- The measurement: `ChangeAreaTimer` = 48 at entry; `Player_X_Scroll` is latched on the GES-3 frame and never
  recomputed, so the screen scrolls ~43 of those 48 frames (ScreenLeft 1216 → 1269) and stops only at the
  level's right edge. Threshold crossing overwrites AreaPointer $2F → $42 permanently.
- So the general rule is `ScreenLeft + 48·d <= 1216` with `d` the entry frame's integer-x advance. That
  *doesn't* over-constrain the user's idea — it prices it: offset ≥ 180 at d=1, ≥ 228 at d=2, on a 256 px
  screen at a 0.65–0.82 px/frame mint rate. Expensive, not excluded.
- **But the rule rejects the WR's own warp.** The delta belongs to a frame the search never simulates: the
  model's goal fires when Mario *reaches* the entry x, and the WR's own goal step advances integer x 1346 →
  1348 (d = 2), while the core's actual entry frame advances 0. Implemented it, the WR's ` GOAL` marker
  vanished, reverted, it came back.
- **The control was not testing the refusal at all.** `--check-path`'s goal flag was `xy_goal(...)` with no
  `goal_refused` (`main.rs:1023`) — so a bad refusal could reject the WR silently and the project's standard
  positive control (F124) would have said nothing. Fixed; that fix is what caught this.
- Net: shipped the control fix and the sound necessary condition; P2.3c-9 Part A is re-sized M–L (a
  case-level change to fire the goal on the entry frame), not the S I estimated. Warp validity stays with the
  core-replay destination gate meanwhile.

**Also corrected:** P2.3c-11's value. It is not the ~1 frame it might find in 4-2 (worth zero there,
quantized) — it is that 4-2 is a validation case with a certified answer across seven single-scalar seams,
so a sub-553 result would be evidence the seams have been leaking frames on every level we called closed,
including 8-4 where one frame is the record.

**Next.** 8-4 primary track: P2.2a-port (unblocked by F130).

### 2026-08-24 — session 16, part 4: the cross-seam test came back uninformative (as pre-registered)

**Did.** Ran the whole 4-2 main area as one bucketed-beam pass from prefix 0, deadline 575, no seams
(`--beam 50 --beam-buckets off,y,spd,sub --beam-max 300000`). Criteria were written into STATUS
*before* the run: >=553 uninformative, ==553 machinery validated, <553 seams were leaking.

**Result (F132).** No goal within 575 steps. 340.9 s, ~280k states/layer over ~12k buckets (per-bucket
width auto-shrunk 50 -> 24). The frontier reached max x 0x53bf0 = 1339.9 at layer 570 — **8 px short of
the pipe at 1348** — and died at 571 on the deadline. So the single-pass beam is >=22 frames worse than
the seven-segment chained 553. By the pre-registered reading that is the **uninformative** branch, and
it stays uninformative: a beam that finds nothing proves nothing.

**What it does tell us.** The seams encode more hard-won structure than I credited — the vine bump, the
plant timing, F115's coupled pit-arc passage — and a naive whole-level beam at 3e5/layer cannot
rediscover it. Widening to the ~1e7/layer the segment searches used, over 575 layers, is ~165 GB of
layer disk. So "dissolve all the seams at once" is not the cheap validation it looked like.

**Corrected design (P2.3c-11a), queued.** Dissolve **one** seam at a time: root on the known chain two
segments back, deadline = those two segments' known combined cost, wide bucketed beam over a
tens-of-layers horizon. Short horizon means the beam can actually be well-powered, and the answer is
informative in both directions.

**Also this session:** runbook §5 Rule 0 (never commit inside the smb-opt clone — it moves HEAD off the
pin, so the patch regenerates EMPTY, applies cleanly, and the Mac silently builds unmodified upstream)
plus `tools/regen_patch.sh` with HEAD/pin, intent-add and shrink guards. Written after a real near-miss.

**Next.** 8-4 primary track: P2.2a-port (unblocked by F130). 4-2 work is gated behind P2.3c-9 Part A,
which is now an M-L case-level change, not the S I estimated.

### 2026-08-24 — session 16, part 5: 8-4 room 3 reduced to one question; H42 born

**Did.** P2.2a′ — the 8-4 room-3 multi-apex seam, enemy-free, with the diversity beam.

**Learned (F133).** The room collapses to a single question. No mint is available in room 3 (census:
max offset 112), so dragging the scroll to 3345 forces x >= 3457. The return bound enumerates 30,720
end classes with costs [33..39] — so **33 is the floor from anywhere**, generalising F125, which only
covered the WR's own apex. And the WR crosses x 3457 at step **161**, finishing at 195: a **34**-frame
return where the cheapest class pays **33**. That one frame is exactly H25's claim, now stated
precisely: *is a 33-cost end class reachable at step <= 161?*

Answer so far: no. 2,303 apex candidates → exhaustive continuation dry (extinct at layer 188). Widened
5x with a finer key and a `vf` axis → 4,333 candidates → dry again, **identical death point and max x**.
Doubling the set changed nothing. Convergent, but layers 1–162 were beamed, so it is not a refutation;
proof-grade needs the exhaustive approach (slack 13 ⇒ cloud-sized).

**H42 (the user's idea, and the best strategic lead on the board).** The record may hide at MrWint's
segment seams, because F66 shows the WR *equals* his segment optima — so the WR is provably no better
than a segment-decomposed optimum, and inherits every loss in the decomposition. Evidence it leaks:
the pipe-clip segments start from **hand-picked mid-air states**; and F66's own table has 1-1 stairs →
grab at 67 segmented vs the WR's 66 — the decomposition lost a frame there.

**H42 sub-check (the user's follow-on: are the seams where the enemies are?) — partially confirmed.**
MrWint's source literally comments a segment "enemy-free (E_CastleArea6: nothing between the pages 8-9
lifts…)", so enemy placement did drive boundary choice. Decoding E_CastleArea6: room 2's middle
(x 1981 → 2373) contains four enemy objects and the clip seam at x 2373 sits exactly between the page-8
group and the page-9 pair. But pages 10–13 hold no enemies at all, so room 3's seams are geometric, not
enemy-driven. Net: enemy-adjacent seams are where generate-and-test buys new coverage — room 2 is one.

**Next.** P2.2f — build a `W84Room2` case (MrWint ships only the two halves), WR-exact + battery, then
dissolve the x-1981/x-2373 seams as one span. 8-4 is unquantized: one frame is the record.

### 2026-08-24 — session 16, part 6: P2.2f opens — room 2's WR route needs an enemy

**Did.** Built `W84Room2` (the room in one span: control row 15917 → the clip pipe at col 152 row 4,
Small Mario, `WithRunningTimer`, `NoScrollPos`, 11-byte key), audited it against the WR, diagnosed
where it stops, and started the enemy port.

**Learned.**
- **The case is exact on the WR for 89 steps** (all of XP/XSUB/XSPD/XFRAC/YP/YSPD/YFRAC), validating the
  start state, terrain and geometry. Room 2 needs **no scroll condition**: its area-change command at
  page 9 col 15 (x 2544) parses at SL ≥ 2241 and the WR is at SL 2316 — 75 px of margin.
- **F134: it diverges at step 90 because the WR STOMPS A BUZZY BEETLE.** YSPD model +4 vs core −4, and
  the beetle at x 2021 flips `Enemy_State` 0 → 4 on that exact frame. So room 2 cannot be searched
  enemy-free — the WR's own route needs the stomp. This is the "enemies are required, not a filter"
  case, and it is H42's mechanism caught in the act: MrWint's seam at x 2373 sits immediately after
  that beetle pair.
- **`$0e` is a jumping Green Paratroopa, not a "lift"** as MrWint's comment claims. Traced from the dump
  (rows 16008–16088): constant x-speed −8 leftward with a repeating parabolic arc 184 → 141 → 185,
  period ≈ 56 frames.
- **Plant/pipe geometry**, derived from the dump as col = (x−8)/16, row = (rest_y−32)/16 and then found
  to be literally the module's own spawn line (`occupy(t, CLASS_PLANT, pc*16+8, pr*16+32)`); confirmed
  by room 3's x-3400 plant landing on (212, 5) = `W84Room3`'s declared pipe. Room 2 = (115,9), (122,8),
  (132,9).
- **Port step 1 shipped: the enemy engine is parameterised on area data.** `Frame` now carries
  `edata`/`pipes` instead of `w42enemies`' hard-coded constants (5 sites). 4-2 passes its own, so it is
  bit-identical — both regressions pass (the `--lift 0` gate, and the enemy-aware core replay of
  `warp87_path.bin` at 87/87 frames, 0 mismatches). 8-4's data added as `W84_ENEMY_DATA` /
  `W84_ROOM2_PIPES` / `W84_ROOM3_PIPES`.

**Three derivation traps burned here (all recorded in the experiment file).** The x subpixel is `$0400`,
not `$0705` (that is the *speed* fraction); the model's `y_pos` low byte is **not** the core's `$0433`;
and `v_force` is an encoded enum, so the core's raw `$0709` = 0 is not a legal model value. The method
that caught all three: run the identical comparison against the known-good `W84Room3` — if it "fails"
too, the comparison is wrong, not the new case.

**Next.** Finish the port: (1) a jumping-paratroopa class, (2) a `w84_enemies` hook wiring `W84Room2`,
(3) difftest the WR's 267 frames to 0 including the step-90 stomp, (4) the d266 search with
`--beam-buckets`. Full plan in `docs/experiments/P2.2f-84-room2-seam.md`.

## 2026-08-24 — session 17 (Track B, SECOND PARALLEL SESSION): P3.2 RAM oracle built and running

**Context.** The user opened a second session to explore Track B while a first session continues
Track A (P2.2f, the 8-4 room-2 enemy port) in the same working tree, and asked whether that can be
done without interrupting the other session — specifically whether the two would have to share the
engine.

**Did.**
- **Answered the parallelism question: no engine sharing is needed.** Track B's next unit (P3.2)
  runs on the QuickNES fast core (`src/fastcore/`, `build/`, `third_party/QuickNES_Core`), not on
  `third_party/smb-opt`. Different tree, different build, different control gate. PROCESS's
  "exactly one machine edits the engine" rule binds `smb-opt` only. The real collision surface is
  **git and the shared docs**, not code — `git add -A` (which PROCESS itself instructs) would sweep
  the other session's in-flight edits, whole-file STATUS rewrites clobber, and both sessions would
  mint F135 next. Protocol agreed with the user and recorded in STATUS "In progress": new files
  only, explicit-pathspec commits, in-place doc edits, **Track A keeps F135+ / Track B reserves
  F200+**, and Track B stays single-threaded + `nice` + `MemoryMax=2G` (the box has 12 cores,
  ~9 GB free, swap exhausted, and Track A's next step wants all 12 threads).
- **Built the oracle** (`src/fastcore/ram_oracle.c`, `tools/build_oracle.sh` — deliberately
  separate from `build_core.sh` so no shared file is touched). Pass 1 records a per-frame RAM hash
  + lives + the victory frame and serializes at `--at`; pass 2 unserializes, pokes one byte, and
  continues on the WR's own remaining inputs until VICTORY / CONVERGED / DEAD / CAP.
- **All four controls pass**: null poke → `CONVERGED(noop)` at frame 0; positive poke
  (`$0770` = 2) → `VICTORY` 2,808 frames early; throughput 14,949 fps ≈ F46's 15.0k; and the core's
  victory frame 17864 = dump 17867 − 3, independently re-deriving F45's row origin.
- **Launched band A** (`$05E0–$06CF`, the only window a proven OOB writer reaches) at 8-4 entry and
  1-2 entry, 61,440 runs each.

**Learned.**
- **F200** — the ending is exactly `OperMode` ($0770) = 2, first at dump frame 17867 = 17848 + 19,
  agreeing with F16/F17 from a completely independent direction.
- **F201** — F43(a) ("WorldNumber ≥ 7 before any castle's axe") **has no target on the warp route**:
  the route contains exactly one castle, 8-4, where WorldNumber is already 7. Sweeping $075F over
  all 256 values there gives 255 DEAD / 1 noop / zero victories. Making it pay needs an *earlier
  castle*, i.e. a routing change, not a RAM write.
- **F202** — the real prize, $06D6 WarpZoneControl in 1-2 (warps to 8-1, skipping 4-1 and 4-2),
  sits **7 bytes above** the block-buffer OOB window's $06CF ceiling. So H7(c) is **narrowed, not
  refuted**, to one answerable question: is P3.1's $06CF reach bound tight? (Plus P3.1 §4's own
  uncovered paths: stack over/underflow, non-indexed writes, `VRAM_Buffer`.)
- Preliminary, ~12 % into band A: **every row so far is CONVERGED** — perturbations to that window
  are absorbed and the RAM re-converges to baseline. If that holds across the band it is itself a
  result (the one proven OOB writer writes into a region the game continuously overwrites), but it
  is far too early to claim.

**Next.** Read the two band-A sweeps when they finish (`grep VICTORY runs/P3.2/*.csv`, then the
outcome histogram); sweep band B (`$0700–$07FF`) at every level entry; re-run anything live-looking
with `--no-death-exit` before claiming (the DEAD early-exit is a stated assumption, not a theorem);
then the ranked cell list → P3.3 and the $06CF-tightness question.
`docs/experiments/P3.2-ram-oracle.md`.

### 2026-08-24 — session 17: P2.2f — the room-2 enemy port lands, and the pipe list was wrong

**Did.** Finished the 8-4 room-2 enemy port (the four steps STATUS listed), validated it, then found and
fixed the bound that makes the room searchable at all. A second session is working Track B (P3.2) in the
same tree; pathspec-only commits, facts split F135+/F200+.

**The port (F135).** The engine stays one module — `w42enemies` is now parameterised on the terrain
(`Slots::step::<B>`) as well as the area, so 4-2 runs `BB42` and 8-4 runs `BB84`. New:
- **`CLASS_PARA`, the `$0e` jumping Green Paratroopa**, derived from the disassembly: `InitJumpGPTroopa`
  (dir 2, x speed `$f8`, and **no `InitVStf`** — its vertical state starts as the slot's stale memory),
  `MoveJumpingEnemy` (downward force `$1c`, dispatched by **ID** so it applies in every state), and
  `EnemyJump` for BG collision (re-launch at y speed `$fd` only when falling onto a solid). Class 8 does
  not fit the 3-bit class field, so it is packed as low bits 000 + byte-0 bit 7 — a code the plant flag
  cannot produce, so every 4-2 record keeps its exact bytes.
- **A stomp rule 4-2 and 1-1 never needed.** `ChkForPlayerInjury` sends a *rising* player to `ChkInj`,
  where an object with id >= `$07` is still stomped when `Player_Y + 12 < Enemy_Y`. That is how the WR
  stomps the room-2 paratroopa while moving up at y speed -4, and a stomped paratroopa demotes to a
  Green Koopa (`ChkForDemoteKoopa`), it does not become a shell.
- **Plant stale memory**: a plant's down/up positions *are* the slot's `$0434`/`$0417`, so they have to
  survive the erase — a paratroopa taking over an erased plant's slot reads the up position as its
  `Enemy_YMF_Dummy`, and every later carry frame depends on it.

**The difftest earned its keep (F136).** The first full battery came back 21/400 divergent, all the same
shape (model stomps, core does not). The core's slots said why: a **fourth piranha plant at col 142** that
the model did not have. `VerticalPipe` adds a plant to **every** vertical pipe outside 1-1 — the only
refusal is all five enemy slots being busy — so the pipe list I had derived from the WR dump was a *lower
bound*. The WR skips (142, 8) and **the clip pipe (152, 4) itself** only because its slots happened to be
full at those moments. With the block-map-derived list the same 400 trials pass clean.

**Validation.** WR 267/267 frames exact against the core (both enemy events, same pipe-entry frame);
reference-path audit `GOAL` at step 267 with **0 bound violations**; 900 random trials / ~171k frames with
**0 differences** (440 stomps, 27 kicks, 204 matching deaths). 4-2 unchanged: the `--lift 0` control gate
is exact and the F127 chain replays 596/596 with 0 mismatches.

**Two things the case needed on the way.** Enemies forced `W84Room2` onto `WithScrollPos` +
`WithBlockStates` (the loader, the offscreen bits, the plant spawns and the timer phases all need them),
key 11 -> 20 bytes; and its start column 136 exposed a latent bug in the *shared* compressed state —
`parser_col` is a `u8` but only 7 bits were packed, so it round-tripped to 8 and the case panicked. 4-2
and 1-1 both start at 24, so nothing had ever noticed. The top bit now goes in one of the two spare bits
at the end of the block-state field, keeping every existing record byte-identical.

**F137 — and this is the part that matters for the search.** The room's bound was the plain x table to
x 2436, and the frontier reaches that **at floor level** ~15 frames before the goal; from there `h = 0`
and there is no signal for the climb the entry actually needs. Measured at the WR's own deadline 267, a
bucketed beam finds no goal at width 50 *and* at width 2000/300k-per-layer — it just races past the pipe.
Fixed with a y-coupled `ygate` bound over the goal's own necessary condition `x >= 2436 && Player_Y <= 64`.
Trap: `steps_xy` never returns 0 (its scan starts at k = 1), so used raw it prunes the WR's own goal —
states already satisfying the condition need `h = 0` explicitly. Audits clean afterwards (0 bound
violations on the WR; 1335 mutation-audit checks, 0 violations, min slack 0).

The climb itself is worth knowing: Mario runs into the clip pipe's **left face**, and because his right
foot point is inside col 152 at row 6 he lands on the pipe's *body* and stands wedged at Y 96, then jumps
to the cap at Y 64 and walks the last 13 px from a standstill.

**Ops.** `model_difftest.py` writes a 33 MB core RAM dump per trial into `/tmp`, which is a RAM-backed
tmpfs here; a 400-trial `--keep` battery filled it and the shell could not `fork` for a minute (every
external command exit 1/134). Recovery is `zmodload zsh/files` + builtin `rm`. Runbook §1 now says to set
`TMPDIR` under `/home` and run batteries under a cgroup cap.

**Next.** The d267 beam control (the pre-registered gate: **d266 means nothing until d267 finds a goal**).
If width alone does not do it, the bucket key has no enemy axis — H40's beetle/plant/paratroopa phase and
slot occupancy — which is the next lever.

### 2026-08-24 — session 17, part 2: two proof-grade verdicts for room 2, and the beam is the wrong tool

**Did.** Searched room 2 with the ported enemies, and diagnosed the search instead of tuning it.

**F138 — `--check-path` is the diagnostic nobody had used on a beam.** It reports, per layer, whether the
reference path is still in the frontier. It says the beam throws the WR away at **layer 40** of 267 from a
step-0 root, and at **layer 41** from a step-70 root — the same ~40 layers in wherever it starts, at widths
50 / 200 / 2000 / 3000 and with a new absolute-x bucket axis. The cause is measurable and constant: rooting
on the WR's own state at steps 70 / 180 / 200 / 220 / 240 gives **14, 14, 14, 14, 13 frames of slack**. An
h-first order therefore prefers, on every layer, the family that is ahead of the WR on x — and the WR's is
behind by exactly that slack. Width and bucket diversity cannot compensate for a loose bound. Also added
`--beam-buckets e` (a coarse enemy-configuration axis, H40) while in there; it was not the blocker.

**F139 — so root on the WR's own state and search the tail EXHAUSTIVELY.** No beam, nothing discarded, so a
dry is a verdict and a goal is a genuine improvement on the WR. Positive control first: prefix 240 at the
WR's own deadline 27 finds goals at layer 27 with 0 bound violations. Then: prefix 240 **d26 DRY**, prefix
220 **d46 DRY**. **The WR's last 47 frames of 8-4 room 2 are optimal.**

And it is not just re-checking MrWint's homework, because I measured where his seams actually are in the
WR: **step 70 (x 1981)** and **step 227 (x 2373)**. The d46 rung spans 220 → 267, so it **crosses the
x-2373 seam** — that is the H42 test for that seam, and the answer is that it does not leak a frame.

The ladder's cost wall is between d46 (209 s) and d56 (9.9M states by layer 14, `pruned 0`); d66 grows
x3.3/layer. F98's law at 14 frames of slack.

**Two corrections the user made, both right.**
1. *"Why must the d267 control pass before running d266? We want a record, not a proof."* Correct — a
   control only tells you what a DRY means; a d266 that finds a path is a record either way, and both cost
   the same. The right move is to run the real deadline with `--check-path` piggybacked. Rule changed.
2. *"Wasn't the plan to put two segments together and beam it with the bucketing strategy?"* Also correct —
   that is P2.3c-11a's shape and I had drifted into a whole-room pass. Relaunched on the measured seams:
   root = the WR's state at step 70, span = his middle + pipe-entry segments in one piece, known combined
   cost 197, deadline **196**. Running.

**And a correction of my own.** I proposed room 3's `build_overshoot_bound` as the fix for the slack; it is
not — that is an x-overshoot-and-return table, the wrong geometry. The slack is located precisely: at the
WR's step 240 the bound says **13** and the truth is **27**, i.e. all 14 frames sit in the last 27. The
bound takes `max(x-cost, y-cost)` as independent when they are coupled — `Y <= 64` is only possible while
standing on the pipe cap (x in [2432, 2464)), and you arrive there at ~0 speed, so the last 13 px are
walked from a standstill while the x table prices them at full running speed. The fix is a small exact
end-game table over the last ~30 frames, indexed by (Y, y_spd, v_force, x, x_spd), built by backward search
on the real model — affordable, since the prefix-240 rung searched that region exhaustively in ~10 s.

**Strategic note (the user's question, worth keeping in view).** The edge is only at the seams. One of
room 2's two is now closed; the 157-frame middle is at the speed cap (F67) and the first 70 frames are
MrWint's own exhaustively-searched segment. If the end-game term does not open the step-70 question, room 2
should be declared closed rather than ground on.

**Next.** The coupled end-game term, then re-run the step-70 cross-seam question exhaustively.

### 2026-08-25 — session 17 (cont.): the allocation was wrong, 1-2 was the level, and it has three real frames

**The user challenged the whole campaign** — we have compute, three days, and a state-of-the-art agent, and
we cannot find a frame that a 2011 TAS did not already have. Two of the premises were wrong and the
conclusion was right.

**Wrong premises.** The WR is 2011, not thirty years ago, and it is itself tool-assisted; and MrWint's
`smb-opt` — *the engine we run* — already brute-forced it segment by segment, with F66 recording the WR at
**gap 0 on all ten segments anyone ever solved**. We are not racing a person with a controller.

**Right conclusion.** Those ten segments are **1-1 ×4, the 1-2 OPENING, and 8-4 ×5** — and F52, written in
P0 and never acted on, says plainly: *"no whole-level or full-state search exists anywhere."* We had spent
the campaign on **8-4 and 4-2**, the two most pre-optimised levels on the route, while **1-2 (deficit 5 on
Maru's route), 8-3 (7) and 4-1 (9) had never been searched by anyone.** That is on me; the priority came
from decisions.md but I should have challenged it instead of grinding 8-4 room 2 all session.

**So: 1-2.** `W12Warp` — the main area in one piece, control frame to the world-4 warp pipe, 1280 frames.
`BB12W` = MrWint's `BB12` (which our dump reproduces with **0 differing cells** over the 176 columns it can
read) plus the eight warp-zone columns he never covered. The goal carries an F40-shaped scroll condition,
because `ScrollLockObject_Warp` arms `WarpZoneControl = 4` at ScreenLeft 2816.

**The model is exact on all 1280 frames** — 6 stomps, the elevator ride, the wall clip, the pipe entry — and
a 150-trial / 96,424-frame battery has 0 differences. Getting there needed two new classes (`CLASS_LIFTPLAT`
for the `$26`/`$27` elevators, which are the same object as 4-2's lift; `CLASS_REDKOOPA`) and turned up **two
real engine bugs, one of them live in 4-2 and 8-4 as well**: `CheckpointEnemyID`'s +8 px applies only to ids
< `$15`, and **bounding boxes were never clamped at the screen edges**, so two goombas 250 px apart turned
each other around. Every prior regression re-verified after both fixes.

**Then the searching.** The `--check-path` loss map is the tool that made this tractable: it shows the WR
losing exactly **66 frames** to the bound across the level, in four places — 11 in the entrance fall, **1**
at step 487, **31 at the wall clip**, 23 at the turnaround — and being **x-optimal on every one of the ~1050
frames in between**. That is a map of where frames can possibly be.

- The isolated frame at step 487: **not there** (d45 dry with the bound tight — a bound artifact).
- The intro area: **not there by construction** — GES 7 for all 335 frames with zero inputs.
- After step 1113: **not there** (d46 and d59 dry, bound tight for the last 46).
- **The wall clip: 77 frames against the WR's 80**, arriving in a state that DOMINATES the WR's, and
  **core-verified 77/77 with 0 mismatches.** Three real frames, on a level that needs five.

**And the scroll takes them back.** The lead survives to step 1217 — the carry is bound-tight and the whole
137-frame segment core-verifies — and then the pipe is dry at 60, the WR's own cost. The reason is that the
warp zone arms on **ScreenLeft**, which is a property of where Mario has *been*: three frames early at the
same x leaves the scroll two pixels behind. The runbook §3.2 census (new `offset-census --sl`, ranking by
absolute ScreenLeft) confirms our continuation came through the scroll-maximal parent, so it is not a
pick artifact.

**Which is why `--goal-sl` now exists** and is running: put ScreenLeft *in* the goal so the search optimises
it instead of reporting it afterwards. Can the clip be done in 79 frames while keeping the WR's own scroll?

**One correction worth keeping.** Mid-session I reported "a goal at layer 47 where the WR takes 48" as a
frame. It was a tie — an off-by-one in the fceux-row -> model-step mapping (step k is row **2486 + k**).
Take reference costs from the model's own `--check-path` numbering, never from a hand-mapped RAM row.

**Also this session:** F139's 8-4 rungs re-verified on the bbox-fixed engine (the control reproduces its
436,334 goal transitions to the digit); `tools/ram_slots.py` had two wrong addresses (EnemyIntervalTimer and
Enemy_YMF_Dummy); 8-3 and 4-1 scanned — 8-3's only blocker is the RNG Hammer Bro, and the 8-4 port already
paid part of its bill by modelling the `$0e` paratroopa; 4-1 has no blocker at all and its block map
extracts cleanly from the **area-load** row.

**Next.** Read the `--goal-sl` run. Then either bank 1-2's three frames, or take 4-1 — the last unsearched
level with no known modelling blocker.

---

## Session 17 (2026-08-25) — the field difftest was lying, twice, and the fix took 1-2 to 1280/1280

**The unit was "fix the parser ordering". There was no ordering bug.** F148 had concluded that `run_step`
updated the area parser too early in the frame. It does not — `player_ctrl_routine()` already runs before
`block_states_game_engine()`, exactly as `GameEngine` does. Two real defects were hiding behind that
diagnosis, and both were things the field difftest **cannot see**:

**F149 — `CheckTopOfBlock`.** At the frame the parser first diverged, Mario head-bumps the **brick at
(68,7)**; the `$c2` is the coin sitting **on top of it** at (68,6). `BumpBlock` and `BrickShatter` both open
with `jsr CheckTopOfBlock`, which erases that coin, calls `RemoveCoin_Axe` (→ `VRAM_Buffer_AddrCtrl = 6` →
the parser stalls) and `SetupJumpCoin`. The model had no such path. Two cells on 1-2's route do it: (60,7)
and (68,7), both confirmed in the core's RAM (block object spawns, `CoinTally` 19→20 and 20→21, AddrCtrl 6).
The other bump-awards-a-coin route, `CoinBlock`, writes **no** AddrCtrl 6 and cannot stall the parser — so
the model is right to ignore it, and 4-2's `$c0` at column 51 costs nothing.

**F150 — `ScrollLock`, which 1-2's entire warp zone runs on.** Column 178 carries a `ScrollLockObject` that
**toggles** the flag, and `ScrollHandler`'s first test is `lda ScrollLock / bne InitScrlAmt` — a set flag
means the screen does not scroll **at all** that frame. The `WarpZoneObject` ($34) clears it and arms
`WarpZoneControl`, **but only on a frame where Mario's Y is even**. And column 198's
`ScrollLockObject_Warp` sets the warp-zone number, kills every piranha plant, and then **falls straight
through into `ScrollLockObject`** — there is no `rts` between them. Without any of this the model's
screen-left ran **2 px ahead of the core for the last 222 frames of the level**, and the goal was
`ScreenLeft >= 2816`: a phantom frame, sitting right where the answer is. The goal is now the exact
`blocks.warp_armed`.

**F151 — the control that should have existed from the start.** `tools/parser_check.py` compares the model
to the core per frame on `AreaParserTaskNum`, `ScreenLeft_X_Pos`, `ScrollLock` and the coin-metatile tally.
1-2 **1280/1280**, 4-2 **587/587**, 8-4 room 2 **267/267**, all 0 mismatches. It is now runbook §3.6: any
case with `BlockStates` on gets it before a search is run on it. Three defects × one unit each is what not
having it cost.

**Re-run on the corrected model.** 4-2's `--lift 0` gate byte-identical. 1-2's 400-trial battery: 58,984
frames, **0 differences**. The clip search redone: **goal at layer 77** against the WR's 80, and this time
the path **core-verifies 77/77 with 0 mismatches**. F142's two rungs still dry at layers 4 and 14.

**F152 — the scroll refund is a tax with a known incidence.** `ScrollHandler` gives the screen one pixel
**less** than Mario moved on every frame his screen position is in [80, 112), and the full amount at 112+;
leftward motion scrolls nothing. So the clip, which moves Mario left, drops him into the taxed band and
charges a pixel a frame on the way out — which is exactly the 3 px that refunded the clip's 3 frames.

**Then the residue, run as one piece.** §21 had named the one experiment left: a search that *optimises the
scroll through the clip* rather than reaching a position gate and checking the scroll after. Chaining
cannot do that, so: steps 1080 → the pipe in **one** search, deadline 199 against the WR's 200, bucketed
beam. Two sizings were wrong first (beam 8 realised 1-2 buckets and went extinct; beam 5000 over five
dimensions dropped the WR's own line at step 32, F138's exact failure mode) before beam **200 over seven**
behaved — 21,743 buckets at layer 88.

**And `--check-path` gave the loss map for free.** Over that segment the WR loses **54 frames against the
bound**, in two clusters and nowhere else: **~30** at the wall clip (Mario is *inside* the wall, his speed
reset every frame, so 11 px take 19 where the x table prices 40 px/frame — horizontal, so a `YGate` is the
wrong tool) and **~21** at the end-game turnaround, taken airborne off a warp-pipe cap. The 88 frames of
open running between them lose **one**. Both want the same construction as 8-4 room 2's missing term — a
small exact table over a localised region by backward search on the real model — which makes `P2.2f-bound`
a **three-level unlock** and the highest-value unblocked engineering item on the board.

**Next.** Read the joint beam. Then `P2.2f-bound`, which is now the thing standing between 1-2 and an
answer rather than a beam-shaped guess.

---

## Session 18 (2026-08-25) — a fresh-look strategy review, and Track E: a finder that runs on the real game

**The user's prompt was not "continue working".** It was: we have failed to find a record over and
over; agents keep answering "search new territory", which abandons ground we may have been close on;
if you truly think no route beats the WR then say so, otherwise work out what *would* find it.

### 1. The review (`docs/strategy-review.md` — now the official plan)
Verdict: **roughly 3-in-4 that a sub-17,868 movie exists**, nearly all of it in 8-4. The evidence for
optimality (zdoroviy_antony's 2019 subpixel rewrite landing on exactly 17,868, MrWint's optimiser
tying the WR on all ten segments it solved, humans matching the framerule in 7 of 8 levels) all
shares one decomposition; it says the WR is optimal *with respect to that decomposition*, not over
all inputs. Diagnosis, in five parts, every one of them visible in this repo's own record: (a) every
decomposition we build is a first-arrival gate and therefore structurally blind to "pay first, gain
later" — rediscovered four times (F115, H39/F128, F143, H42); (b) the bottleneck is the state space,
not the bound (the other session's `P2.3e` §41 settled this the same morning); (c) the searches
optimise the wrong scalar (time is worth zero inside a framerule — H41, written down, never built);
(d) effort went where the frames are not — the two biggest non-movement pools on the route
(1,492 frames of countdown, ~700 of intermission card) had never been audited, and both are rigid;
(e) the unit loop rewards turnover, and the cheapest verdict is a beam.

**User doctrine change, recorded:** proof and exhaustiveness are no longer deliverables. Only
positives get verified.

### 2. The finder (`src/fastcore/explore.c`, `tools/build_explore.sh`)
Archive-based exploration (Go-Explore) **on the QuickNES core**, i.e. on the real game: no model, so
the F147/F149/F150 class cannot occur and every path is core-verified as produced. Cells are a
coarse projection (x, y, x-speed, Player_State, **rel = x − ScreenLeft at 2 px**, a scroll-frozen
bit, AreaPointer, GES, enemy digest); best-per-cell is kept and **any cell can be resumed at any
time — there are no layers, so the H39 defect is impossible by construction.** `--seed-wr` seeds the
movie's own continuation so the run starts from an incumbent; `--seed-path` seeds a search artifact
(the 553-frame 4-2 chain); a **null-coast probe** implements F17's objective directly (release every
button and see whether Mario still finishes); `--goal-ram`/`--require-ram` give arbitrary goals and
sound invariant pruning; `--watch-x` prints a cost curve. Control: it re-derives F223's last-input
17846 from scratch.

### 3. What the cheap checks settled
- **F224 (E1)** — level-entry state is a pure function of (entry frame, area-load count). **H9/P2.4
  refuted.** Corollary: every area load costs exactly one lag frame and **four are inside 8-4**
  (H2 reopened, sharpened, low prior).
- **F225 (the cap survey, `tools/cap_survey.py`)** — the WR is at the relevant speed cap for 80–97%
  of every level's control frames. **4-1, 8-1 and 8-3 are at 97%** and their off-cap frames are the
  single forced acceleration after the level-start card, against deficits of 9/18/10: **those three
  cannot deliver a framerule from movement at all.** This retires "go search a level nobody has
  searched" and retrospectively justifies the concentration on 1-2 and 4-2.
- **F226** — 1-2's "unexplored 540-frame intro" is 499 frames with the joypad overridden. Not
  territory. Maru's 3 frames are in the modelled body.
- **§4 of the review** — the countdown and the intermission card are rigid at code level
  (`DigitsMathRoutine`'s Y is constant at every call site; `DisplayIntermediate` is gated on
  `AltEntranceControl`/`AreaType`/`DisableIntermediate`, none of which a warp can set).

### 4. 4-2, taken to the code
- **F228** — the wrong warp is a race against one area-change command (`page 5 col 15 -> $42`), and
  there is exactly one enterable pipe before it. The destination flips the frame `ScreenLeft` hits
  **1217**. WR: x 1348 / SL 1216 / rel 132. The 553 chain: x 1349 / SL 1237 / rel 112 → `$42`.
  **H37 refuted** (cols 78–79 is a decoration pipe; `VerticalPipeData` gives its top `$13/$12` and
  `HandlePipeEntry` demands `$11`/`$10`).
- **F227** — **every** way to freeze the SMB1 scroll, enumerated from `ScrollHandler`. 4-2 has only
  `SideCollisionTimer`, whose sole writer `ImpedePlayerMove` zeroes `Player_X_Speed` on the same
  path. **H38's proof artifact, and it is negative.** What stays open is *where* the mint is paid.
- **F229 — the scroll law:** `ScreenLeft <= (largest x ever reached) − 112`. It governs both attacks
  in opposite directions.
- **Measured (`runs/E3-w42/r460.log`, the "mint cost curve" the 4-2-hope thread says was never
  taken):** a genuinely warp-capable entry (rel ≥ 132 **and** `Player_X_Scroll == 0`, the second
  condition being why F129's candidate failed) is reachable at core frame **~7195**. The 553 chain
  enters at 7134 and a framerule needs **≤ 7156**, so the key budget is 22 and the measured key is
  ~61. **This is the first real number for that question and it is discouraging.**

### 5. 8-4, and a mistake worth remembering
- **F230** — 8-4 is a maze built out of area-change commands; most of its pipes send you back to
  page 1. My first pass used `GES == 3` ("a pipe was entered") as the goal and **immediately
  reported −54 frames in room 3 and −102 in room 2. Both were wrong-pipe entries.** Same defect as
  F129/F131, in a new place. The goal is now the destination (`GES 7` + `alt 2` + the next room's
  page + `X 56`) and all four controls reproduce their baselines.
- **F231** — 8-4 room 1 is a full lap of a *looping* corridor: Mario sprints x 40 → 1270 at the cap,
  the coordinates wrap (x 1270 → 261, ScreenLeft with it), and the pipe is 6 frames later. The lap
  is forced because the parser must read `page 5 col 3 -> $65/7` (at x ~1150, so `max_x >= 1135` by
  F229) before the pipe will open on room 2. **No turnaround, pure running at the cap: closed.**
- Room 3 *is* a scroll-gated turnaround (run to x 3456 to parse `page 14 col 4 -> $02`, then back to
  the pipe at x 3404); F229 makes the overshoot minimal, so only the **return leg** is searchable.

### 6. Running
Five archives: `runs/E3-w42/r460.log` (4-2 mint curve) and `runs/E3-w84/{room2,room3,water,bowser}.log`.
The water room is 696 frames nobody has ever searched; `bowser` uses the last-input objective (F17).
**Next:** read the curves; if 4-2's stalls far above 22, retire it and put everything on 8-4, where
one frame is the record.

### Session 18, continued — the rest of the day (everything after the entry above)

The first entry stops at F231. What follows is the larger half.

**The finder grew into a general instrument** (`src/fastcore/explore.c`, `tools/build_explore.sh`).
Added through the day, each for a reason: `--seed-path` (seed a search artifact, e.g. 4-2's 553
chain); `--goal-ram` / `--require-ram` (arbitrary goals and *sound invariant pruning* — a state whose
warp destination has already flipped can never satisfy the goal, so never archive it);
`--watch-x` (a cost curve — earliest frame at each screen-lead inside a window); `--max-addr`
(maximise a RAM byte, put it in the cell key); `--anomaly` (P3.4, self-calibrating novelty);
`--subcell`/`--ysubcell` (the horizontal/vertical subpixel in the cell key). Plus
`tools/e3_replay.py`, `tools/cap_survey.py`, `tools/entry_state_scan.py`, `tools/down_sweep.py`.

**Three proxy-goal traps in one day — the single most important operational lesson.**
1. 8-4 with goal `GES == 3` ("a pipe was entered") reported **−54 and −102 frames**; both were
   wrong-pipe entries into 8-4's maze (F230).
2. 8-2 with goal `GES == 5` reported **−51 frames**; replaying it showed the level ending **+126**,
   because that path takes a normal pole slide while the WR's flag glitch skips it (F237).
3. F131 had already done this to the project before I arrived.
**Rule, now written into `P4E-finder.md`: the goal must be the quantity the record is measured in.**
Flag level → `StarFlagTaskControl == 5` (the area change). Pipe level → the entry that sets the next
`WorldNumber`. 8-4 → the last input. And it must be *monotone with the record* — checked and shown
for 1-2 in STATUS.

**What got closed, and how.** Almost every result came from reading the ROM and censusing the WR
dump, not from compute:
- **F225 the cap survey** — the WR is at the relevant speed cap for 80–97% of control frames in every
  level; 4-1/8-1/8-3 are at 97% and **cannot deliver a framerule from movement at all**.
- **F226** 1-2's "unexplored 540-frame intro" is 499 frames with the joypad overridden.
- **F227 / F229 / F236 the scroll law** — every way to freeze the scroll, enumerated; `ScreenLeft <=
  max_x − rel`; 1-2's clip *is* a scroll mint and its lead is exactly neutral. This one law governs
  the endgames of 1-2, 4-2 and 8-4 room 3 and is why the record is hard.
- **F228 / F230 / F231 / F232 / F233** — 4-2's wrong warp is a race against one command with exactly
  one enterable pipe before it (H37 refuted); 8-4 is a maze of area-change commands; 8-4 room 1 is a
  forced lap; **8-4 is closed on movement, route and structure**; the bonus-room detour is worth 292
  frames in 1-1 (taken) and a 226–379 frame loss in 4-1/8-1/8-2 (correctly skipped).
- **F235** — worlds 8-7-6 is `WarpZoneControl` row 6, which needs `AreaType == 1`, and `AreaType` is
  stamped at load. **1-2 can never legitimately produce it.** The 3,957-frame prize is closed on the
  legitimate path; it survives only as H7(c)'s OOB write. Restated sharply in `warp-model.md`: the
  ask is **one more `inc $06D6`**, not an arbitrary write.
- **F234** — F221's ceiling argument was about the wrong mechanism (the VRAM offset accumulates
  *across* frames, gated by `VRAM_Buffer_AddrCtrl`), but the verdict survives; measured max 67 vs 227.
- **F240** — the area parser runs a *constant* 22–24 columns ahead of `ScreenLeft`, so stalls cost
  nothing. Killed the "avoid the coin bumps" idea before a search was spent on it.

**Merged from the Mac session** (staged file, now deleted): **H46** the wall-face census, **H47** the
speed-cap premise behind every closure, a **correction to F224** (`PlayerSize` $0754 and
`PlayerStatus` $0756 are above the clear line, path-dependent, and change collision geometry — the H9
refutation survives, the parenthetical did not), and **F238** (the WR is small Mario on 18,264 of
18,268 frames). Verifying their H46 write-up produced **F239: the walk-through primitive runs at the
FULL SPEED CAP** — the WR walks through solid row 10 in 4-2 from col 33 to col 49 with x-speed pinned
at 40. That is the fact E7's whole premise rests on.

**Two doctrine changes from the user.**
1. *Find, don't prove* (morning): proof and exhaustiveness are no longer deliverables; only positives
   get verified.
2. *Banked frames count* (afternoon): a sub-threshold gain still reduces a level's deficit
   permanently. STATUS now carries a banked-frames table. He also corrected a real error — 4-2's 35
   frames are a **conditional asset, not banked**, because that route never reaches 4-2's endpoint
   faster, it sprints to the pipe and warps wrong. **Banked total across the route: zero.**

**Strategic assessment, stated so it is not lost.** SMB1 is the hardest target in the medium, not the
easiest: 32 KB of code, eight levels, fifteen years of the best TASers, MrWint's optimiser, and an
independent 2019 subpixel-perfect rewrite that landed on *exactly* 17,868. It is not scrubbed, but
the remaining surface is small and specific, and **the productive method is reading the ROM plus
targeted measurement — searches are a finishing tool, not the discovery engine.** One day of reading
closed more than seventeen prior sessions of searching. What is genuinely left, in order of odds:
**(1) the H46 wall-face census** — a proven full-speed primitive whose applicable set has never been
enumerated, the only class that yields *distance* rather than fractions of frames; **(2) the
unaudited half of the ROM**; **(3) 1-2's eight frames**, where the lever is identified. Falsification:
if the census comes back empty at both hitboxes and the audit is clean, SMB1 any% is optimal and that
is itself a publishable result (PLAN §7 tier 1).

## 2026-08-25 — session 19: E9a, the wall-face census (empty), and the 114 frames it found instead

**Did.** E9a end to end, exactly as STATUS specified it: no emulator, no compute, one afternoon of
disassembly plus `data/wr/fceux_wr.ram`. Four new tools (`tools/route_blockmaps.py`,
`wall_face_census.py`, `route_loss_map.py`, `route_obstacle_cost.py`), block maps for all fourteen
controllable route areas (`data/blockmaps/`), the write-up in `docs/experiments/P4E-census.md`, and
F241-F245 + H48. The four `build/explore` archives from session 18 were left running untouched;
none has beaten its control (see STATUS "Running jobs").

**Learned — the census is empty, and the mechanic was being described wrongly.** 708 wall faces
across the route, **zero** admit a static walk-through at either hitbox (F243). The reason took
re-reading `DoPlayerSideCheck` line by line: *blocking is "non-empty", not `CheckForSolidMTiles`*
(F241) — that routine is a head-bump classifier, and the 4-2 bricks the WR famously walks through
are `$52`, which it calls *not* solid. The loop exits at the first probe that finds anything and
`ImpedePlayerMove` reads the counter it exited on, so a **left** probe in any non-empty cell is a
free pass. That makes the entry test simple and the answer negative: the left probe sits in the
column before the face for a full **11 px**, so the tile there must be non-empty *and survive*, and
**only `$5f`/`$60` do — all nine of which are isolated on this route.** A coin cannot: the right
probe collects it eleven pixels before the left probe needs it (F242). That is the missing *why*
behind F93's 31 frames, which the project has been recording as a measurement for five sessions
without explaining.

**Learned — the live primitive is vertical, not lateral** (F244). `ChkFootMTile` ends in a **`jmp`**
to `ImpedePlayerMove`, so a frame whose feet are inside a non-empty cell with `Y & $0F >= 5` returns
without ever running the side check; with `Player_MovingDir` LEFT and speed >= 1 it does nothing at
all. The way into a wall is to sink into its top, not to walk into its face. Two more total-skip
conditions fell out of the same read: `Y >= $cf` skips all of `PlayerBGCollision`, and `Y < $08`
makes the side check leave before any probe.

**Learned — the part that actually moved the board.** The census needed a value filter (a
walk-through only pays where the route is off the cap, since SMB1's airborne x-cap equals its ground
cap), so I priced every off-cap stretch of the WR against 2.5 px/frame. **The whole geometric loss
of HappyLee's run is 290 frames** — 324 more are the sixteen forced post-card ramps — **and 114 of
those 290 sit at one place nobody in this project had ever priced: 8-2's columns 201-212** (F245).
A one-column pillar, a two-column bottomless shaft, a two-column wall from row 3 to row 12: he falls
into the shaft and **wall-jumps** up it, 183 frames for 173 px against a 69-frame bound. Its faces
refuse and F244's sink cannot reach it, so it is a **jump-arc** problem — and on his own measured
full-speed arc the direct jump from the pillar misses by **one to two pixels** (H48). Also worth
saying plainly: **8-1, 8-3, 4-1 and 1-1 have no priced geometric loss at all**, which independently
confirms F225 and closes geometry as a lever on four of the eight levels.

**The method note, since it keeps repeating.** Session 18's lesson was "reading the ROM beats
searching it". This session's is narrower and sharper: **the filter you build to rank a hypothesis
can be worth more than the hypothesis.** E9a's own answer is a clean negative; the ranking machinery
it required found the biggest unexamined number on the board. And the running `e8-climb` archive has
been searching that exact region for two hours with a cell key (`--xcell 6 --ycell 12`, no subpixel)
that is **provably below the resolution of the question** — the same defect the Mac session caught in
1-2. Check that a search *can represent* the thing you are asking it for before you spend six hours.

**Next.** E9b-1: `./runs/E9b/launch.sh` (written, committed, rooted at 12157 before the approach
jump, `--subcell 16/32`). It is blocked only on RAM — 1 GB available of 15 with four archives
running — so it waits for `pgrep -x explore` to empty. The zero-memory fallback is to splice a jump
into the WR inputs at dump row 12289 and replay on the core, which tests H48 directly.

**Later the same session — the user asked the question that fixed the unit.** *"Did you successfully
clip walls that we know the public has already clipped? If not, your strategy probably sucks."* I had
not, and that was a real hole: a census whose classifier is never made to reproduce a clip somebody
has demonstrably done is worth nothing. `tools/clip_control.py` now does it, using HappyLee's own run
as the corpus. It finds him embedded in terrain for **272 control frames in 14 episodes**, the two
long ones being exactly the known clips (4-2's 151-frame wall walk, 1-2's 94-frame clip), and it
reproduces **1-2's entry frame for frame**: impeded at speed 40 the instant the right probe touches
col 168, `Player_MovingDir` flipped LEFT, `Y & $0F` = 6,7,9,11,13, **+1 px per frame for 14 frames**,
left probe crossing at 3586, then re-acceleration inside the wall. **The control passes — and it
corrects the unit's headline.** The census's finding is not "no clips exist"; it is **"no face admits
a *full-speed* lateral entry"**. Every clip that happens pays 40 → 0 → re-accelerate, which is
precisely *why* 1-2's clip costs 33 frames and 4-2's costs 31. That is a better fact than the one I
had, and I would not have had it without being asked (F246).

**The 8-2 site, taken to the core.** Rather than wait for a search, I spliced a jump into the WR's
own inputs at the pillar and replayed. **It clears the wall** — x 3283 at Y 53 against the Y ≤ 55 the
geometry needs, speed pinned at 40 through both columns, on the floor at col 214 by core 12348 versus
the WR's 12458, **reaching the flagpole 112 frames early**. My hand-traced arc estimate ("misses by
1-2 px") was **wrong**; it clears by 2 px, which is the argument for replaying instead of
transcribing. **But it is not a record**: every variant grabs the pole with a normal slide, while
HappyLee touches it at Y 165-166 and goes GES 8 → 5 in one frame with `StarFlagTaskControl` jumping
0 → 2 — the flag glitch. Best probe `$0746 == 5` at core 13015 (+63), typical 13078 (+126) — **the
same +126 the E8 launcher header already records from its own proxy-goal trap.** Third time this
project has walked into F230/F237; the goal check caught it again. What is left is genuinely
promising and genuinely small: a **~4 px band in `Player_Y_Position`** at the frame `x+13` crosses
into column 216, on a line carrying 112 frames of slack (F247).

**And the Mac is now a Track E machine (F248).** The user pointed out the Mac is available and
wondered whether the new fast-core tooling could move there. It can, easily: `build/explore` and
`build/harness` are single portable C files over the libretro core with **no `smb-opt` patch
dependency at all**, so PROCESS's container requirement and `mac_run.sh`'s stale-engine guard simply
do not apply to Track E. `make platform=osx` for QuickNES, plain `clang` for both binaries, **zero
source changes** — and the control is the strongest kind available: the 13,000-frame WR RAM trace is
**byte-identical** across the two machines. It runs at **20,063 fps against this box's 6,479 (3.1x)**
with 18 GB free. E9b-1 is running there now, which is what unblocked it — the Linux box was at 1 GB
available with four archives going. Gotchas recorded: no `git pull` over BatchMode SSH (keychain), and
no cgroups on macOS, so the never-uncapped rule is met by `explore`'s fixed-capacity archive plus an
RSS watchdog.

**Then the user's transition-screen question, raised and closed inside an hour.** He asked what about
the screens where Mario walks into a pipe, and warned me — correctly, and about a mistake I had just
made — not to judge an idea by whether it fits the WR's route: *"if we find some crazy jump, that's
live as it gets regardless of where it is."* I had read "the WR's inputs die after the poke" as "dead",
when what it actually meant was "Mario is somewhere else now".

The measurement: **8-4 spends 384 frames on entrance animation** — each of its four sub-area loads
parks Mario in `PlayerEntrance` for exactly 96 frames sliding him up out of a pipe 1 px/frame from
Y 240 to Y 145, control at load+122 against load+43 for every mode-0/1 entrance on the route (F249).
The branch is three instructions in `VerticalPipeEntry`, and `WarpZoneControl != 0` overrides it. And
the byte that sets `WarpZoneControl` is enemy routine `$34`, fed by `$06CB` — **which is inside
F203's proven `$06CF` OOB ceiling, unlike `$06D6` itself** (F250). We had been aiming at the byte we
cannot reach while a byte we can reach did something worth 79 frames a firing.

Then I stopped deriving and measured it: added `--poke ADDR=VAL@FRAME` to `build/harness` and poked
`$06D6` 22 frames into the 48-frame descent. **It works exactly as predicted — `PlayerEntrance` runs
1 frame instead of 96 and the pipe destination is unchanged** — and it is still **42 frames worse**,
because `AltEntranceControl` = 0 is the only mode that can show the world/lives card and
`DisplayIntermediate` shows it *unconditionally* on castle levels, bypassing `DisableIntermediate`
(the ROM calls that branch "possibly residual"). 137 against 96. **H49 refuted, F251.**

Two things survive. The re-pricing of the OOB target (`$06CB`, inside the window) stands on its own.
And there is one exact residual: 8-4's water-room transition has a non-castle *destination*, so
`DisplayIntermediate` there does consult `DisableIntermediate` — `$06D6` plus `$0769` during that one
descent is ~96 frames. Both bytes are out of proven reach, so it is an E10 target, not a testable
hypothesis.

**Worth keeping as method.** This is the second time today that building the measurement rather than
trusting the derivation changed the answer — the 8-2 arc estimate said "misses by 1-2 px" and the
replay said "clears by 2", and here the code read said "+79 frames" and the poke said "−42". Derive to
find the question; measure to answer it. `--poke` now exists precisely so the next one is cheap.

## 2026-08-25 — Session 20 (Mac): E10, the ROM read end to end
**Did.** The user asked for a full attack on the disassembly — "AI is good at relationships between
different parts of source code" — which is exactly open-threads Tier 2 #3 (E10). Read all 16,351
lines of `smbdis.asm` with the WR dump open beside it. Started from a checkout five sessions stale,
did the read independently, then reconciled against F203-F251 and dropped everything that merely
re-derived an existing fact. **Three results survive, and the first one closes the board's top lead.**

**1. H43(b) is refuted at code level (F252) — and F210/F216 are wrong.** Both of those facts solve
`HeadChk`'s own guard (`cmp PlayerBGUpperExtent,x`) and stop there. But `HeadChk` is not an entry
point: `PlayerBGCollision` has exactly one caller, and `ChkCollSize`/`HeadChk` are reachable only by
falling through `ChkOnScr` twenty lines earlier, which requires **`Player_Y_HighPos` = 1 AND
`Player_Y_Position` < $CF**. Every Y in F210's {$FE,$FF} and F216's $DE-$FF windows is >= $CF and
returns before the head check exists; and "Mario above the top of the screen" is `Player_Y_HighPos`
= 0, which fails the other guard. Over the real domain the head row is $00-$C0 for every
size/crouch/swim combination, and the feet (`cmp #$cf`, adder $20) and both side probes (`cmp #$20`
adders $08/$18; `BHalf`'s *lower* `cmp #$08` with adder $18, and $08+$18 = $20 exactly) close the
same way. **No player-driven block-buffer access in the game can leave the buffer.** With F203
(address ceiling) and F215 (value set) the block-buffer OOB mechanism is now closed on both axes.
The one genuinely unguarded writer is the *enemy* path — `HandleEToBGCollision` at
`Enemy_Y_Position` 6-7 does reach row $F0 with no `cpy #$d0` — but it writes only `$00`, which F215
already showed is inert as an `Enemy_ID` (F253). Its one non-inert clear is `$06CC SecondaryHardMode`,
which would suppress unparsed hard-mode enemies — 8-3's Hammer Bros.

**2. The framerule is one enemy slot's interval timer, and a second star flag deletes it (F254,
H50).** `RunStarFlagObj` is dispatched once per frame *per enemy slot* holding `Enemy_ID` = $31,
but the state it drives is global — **except the one byte task 4 blocks on, which is per slot.** So
with two star-flag objects: task 2 subtracts two timer units per frame (countdown halves), and task
4 reads the second object's never-written `EnemyIntervalTimer` = 0 and advances to task 5 in the
same frame, so F27's (v+1)+105 wait — which *is* the framerule — becomes 1 frame. Priced at N=2:
**~1,319 frames, and all five flag levels become unquantized like 8-4.** Today exactly one exists
per level because of a single `beq` in `CastleObject` (`lda CurrentPageLoc / beq ExitCastle`) —
4-1, 8-1, 8-2 and 8-3 each carry a *second* castle object at page 0 column 0 that it suppresses.

**3. H3 closed (F255).** `TimerControl` really does shift the ITC grid relative to the level (unlike
pause, F62): non-zero skips `IntervalTimerControl` while `FrameCounter`, the LFSR and the game logic
keep running. The arithmetic: Δ = c + ((v0 + k − c) mod 21) − v0, so a gain needs
c + ((k−c) mod 21) < 21, and the freeze must sit between the level's load and its T_set. The only
writer is `SetPRout` (`ldy #$ff`), and the only freeze during which Mario still moves is
`PlayerInjuryBlink` (k = 55, c = 16) → **+13 frames at best.** Refuted for every reachable freeze.

Also measured for the strategy picture (F256/F257): **the non-gameplay budget is ~4,770 frames,
26.7 % of the movie**, against 290 frames of movement loss route-wide (F245) — 1,471 in level-load
screens, 2,787 in the end-of-level sequence (1,497 of it the timer countdown alone), 512 in pipe
timers. The intermission card costs exactly **127 + w** per showing, eight showings, **1,097 frames**;
both skip flags are structurally 0 at every one of them, with `$0769` having exactly one writer in
the whole ROM. Plus the smaller ones: the game-timer carry-over is a net zero, not a lever; every
bound we quote needs a 24-frame tick caveat; the side-pipe `ChangeAreaTimer` is 160 vs 52 on
`ScreenLeft_PageLoc`; a misaligned `AreaDataOffset` would be immediate ACE.

**Learned.** The guard that mattered was twenty lines above the routine everyone had analysed. Two
sessions' worth of ACE work priced a window whose writer does not exist, because the derivation was
scoped to the routine rather than to its call path. Worth a habit: **when a fact solves a guard,
check what guards the caller** — `grep -n '<label>' ` on the label first, then read up from the entry.

**Next.** The cheapest thing on the board is now H50's poke test: `build/harness --poke` already
exists (F251), so `Enemy_ID+k = $31` / `Enemy_Flag+k = 1` before 1-1's grab and read the next
area-load frame settles a ~1,300-frame claim in about twenty minutes. Then E10's second pass — the
`VRAM_Buffer` overflow class is now the only thing H43 still rests on.

## 2026-08-25 — Session 20 (Mac, cont.): H50 measured — 1,329 frames, and the framerule is gone
**Did.** User: stop discussing, run it. So I ran it. `build/harness --poke` existed but the Mac's
binary predated it — rebuilt (`clang -O2 ... harness.c`), then raised the poke cap 8 → 64 so N > 2
fits, then wrote `tools/starflag_poke.py`, which does a control pass with the unmodified WR inputs
and a poked pass in the same invocation so the control is part of the measurement rather than a
memory.

**It works, first try.** 1-1, poking `Enemy_ID+1 = $31` / `Enemy_Flag+1 = 1` (plus the star flag's
coordinates) eight frames after the real flag spawns: countdown **371 → 185** (halved to the
frame), and `DelayToAreaEnd` advances at core 1676 with `EnemyIntervalTimer[0]` **still reading 4**
— the framerule wait, bypassed, observed directly. Next area load 1941 → 1677, **264 frames**.

Across all five flag levels at N=2: **857 frames**. Then the shape of the remainder showed up: 8-1
only gained 78 and its wait *grew* (109 → 132), and N=3/4/5 changed the countdown but not the exit
frame at all. The new floor is `DelayToAreaEnd`'s second condition, `EventMusicBuffer == 0` — the
win music, whose length is fixed. `PlayerEndLevel` queues it only if `ScrollLock` is still set when
Mario passes Y ≥ $ae, so `--no-music` clears `$0723` one frame earlier: **`StarFlagTaskControl` then
goes 3 → 5 in a single frame, task 4 skipped entirely**, and the five levels give
312+289+210+278+240 = **1,329 frames**. F259/F260. (The Linux session, having picked up the E10 push,
ran the same N=2 test independently within the hour and got the same 857 — that is F258, `tools/starflag_probe.py`. Independent agreement on the number, which is worth more than the duplicated effort cost.)

Health-checked past the early exit rather than assuming: 1-2 loads at 1629, runs its intro, hands
off to the main area at 2125 through the normal `ScreenRoutineTask` 6 → 8 sub-area path, control at
2150, timer reloads to 400, lives unchanged, no reset.

**Learned.** Two things beyond the number. (1) **The framerule disappears in every level where this
fires** — with the wait at 0 the exit is `grab + 126 + ⌈T/2⌉ + 1 + 32`, all frame-granular, so
open-threads' budget table ("a level only pays if it saves its whole deficit") stops applying and
the 78 frames of per-level deficit plus every banked sub-threshold frame come back to life. That is
worth more than the 1,329. (2) **Reachability is now the entire question and it is sharper than
before** (F259): both halves need one non-zero write — $31 into a spare `Enemy_ID`, and `$0723` = 0
— and neither has a writer (the frenzy cells are unreachable after F252; no flag level contains a
`ScrollLockObject`). So H50 is not a separate lead, it is **the payoff attached to H43's missing
primitive**: the ACE line went from "a confirmed jump with no known payoff" (F208) to "one known
byte into one known cell is worth 1,329 frames".

**Next.** The three write classes P3.1 §4 never audited are now the whole game: stack
over/underflow, non-indexed writes, and `VRAM_Buffer` overflow (indexed by `VRAM_Buffer1_Offset`,
which `GetPlayerColors` +7, `WriteBlockMetatile` +10 and `OutputNumbers` +3 all advance and only
`ColorRotation` bounds). That is E10's second pass — pure reading, same shape as the one that
produced F252-F257.

## 2026-08-25 — Session 20 (Mac, cont.): E10 passes 2 and 3 — H50 and the whole ACE line close together
**Did.** User: keep going on the write classes; and, on `CastleObject` being the only `$31` writer,
"how do we make the things that allow us into the guard?" Both got answered.

**Pass 2 — the zero page, a class no audit had ever read.** `Enemy_ID` is `$16` and `Enemy_Flag` is
`$0f`: H50's target is in the **zero page**, and `tools/oob_audit.py` *excludes zero-page bases by
construction* because every prior audit aimed at page-6/7 targets, for which the zero-page wrap
makes them unreachable. Added zero-page target support to the tool. 320 stores can reach
`Enemy_ID`; 299 need an index >= 7 that nothing takes. The decisive move was enumerating the other
side — all 16 stores into `Enemy_ID` and the value each writes: **`CastleObject` is the only
instruction in the ROM that writes `$31`**, the two frenzy cells are the only variable-valued
writers, and the remaining thirteen are compile-time constants. F261.

**The user's castle question, across all 34 areas.** The guard isn't the obstacle — it only
suppresses the *page-0* castles, so the real question is whether a non-page-0 castle can render
twice. Decoded every area: each ground level is `[page-0 castle, end castle]` or `[end castle]`,
and **no area in the game has two non-page-0 castles**. The only level-data re-parse mechanism,
`ExecGameLoopback`, is driven by `LoopCmd` objects that exist only in 4-4/7-4/8-4 — no castle
object, no flagpole. Entering at a non-zero `HalfwayPage`/`EntrancePage` does make `CurrentPageLoc`
non-zero, but then `CheckRear` skips the page-0 castle as behind the renderer. F263.

**Pass 3 — the last two classes, and the closure.** `VRAM_Buffer` overflow: largest displacement in
the ROM is **+27**, so with an 8-bit index the ceiling is `$041B`/`$0444` — page 4, 647 bytes short
of `$06CB`, however far the offset runs. Stack: `$0100+S`, 8-bit S, page 1. **Neither class can
reach the target at all.** Then the complete writer set of the frenzy cells: 30 indexed stores
(all needing indices of 42/29/13 against loop bounds of 11/13/5, plus the block-buffer family
already closed by F252/F253) and 13 absolute stores whose values are `$00`, `$12`, `$15`, `$16`,
`{$14,$17,$18}`, and `InitEnemyFrenzy`'s `lda Enemy_ID,x` — which is only ever dispatched for IDs
`$12/$14/$15/$16/$17`, so it copies one of those to itself (`$31` maps to `NoInitCode`).
**`$06CB` in {$00,$12,$14,$15,$16,$17}, `$06CD` in {$00,$14,$17,$18}.** F262.

**So H50 is unreachable, and H43 closes with it by the same enumeration.** F207/F208 saw the
out-of-table jump *fire* when `$06CB` was poked to `$c4` — but `$c4` is not writable, and neither
is anything `>= $37`. **The arbitrary jump exists and can never be armed.** open-threads #8 and #4'
both close.

**Learned.** The thing that unlocked pass 2 was noticing the target's *page*, not its name: two
sessions had been hunting a write into "the frenzy cells" while H50's actual requirement was a
zero-page byte, and the tool everyone was using filtered zero-page bases out by design. Worth
generalising: **when a hypothesis names a cell, check which page it is in before reusing an audit
that was built for a different page.** And the enumeration beat the search twice today — census the
writers of the target rather than bound the indices of 299 stores.

**Next.** Residuals are named in F262 and are all narrow: the `MetatileBuffer` start-row overrun
(ROM-fixed, inferred from the game not crashing rather than decoded per object), a misaligned
`AreaDataOffset` (nothing misaligns it), and power-on state (H20). Otherwise the state surface is
now as closed as the movement surface, which is exactly the condition `open-threads.md` calls a
defensible stop — that is a call for the user, not for me.

## 2026-08-25 — Session 20 (Mac, cont.): the board made legible, and H2 closed
**Did.** Two things the user asked for. **(1) Made the documentation match reality.** I had been
answering "what's left" by reading and inferring, which meant it was not actually written down.
Rewrote `docs/open-threads.md`: it led with four tiers of 21 items, half of which closed today, so
it now leads with **the live board** — a table of the remaining items with what each needs, what it
has, and whether it is running — and files everything closed at the bottom with its date and fact
number. 180 lines → 119, and a fresh reader sees the state in one screen.

**(2) H2 — the lag-frame read, and it did not go the way the prior said.** 17 lag frames on the
route (not 16 — F224 corrected), all at exactly `load + 2`, **five inside 8-4** (the earlier list of
four omitted 8-4's own main entry). A harness `ScreenRoutineTask` dump gives the sequence
`ChgAreaMode` → `InitializeArea` → *lost NMI* → `InitScreen`, so **the overrunning routine is
`InitializeArea`, not `InitScreen`** as `timing-model.md` §1 has said since P0.5. The cycle count
settles it: `InitScreen` fits comfortably (`MoveAllSpritesOffscreen` 1,024 + `InitializeNameTables`
18,432 ≈ 21,500 of 29,780 — and while counting it I found its `InitNTLoop` writes **960** tiles per
name table, not the 768 its own comment claims, because `ldy #$c0` is set once and `dex / bne
InitNTLoop` re-enters with y = 0). `InitializeMemory` does not: 18 cycles per byte over 1,868 bytes
= **~33,370**, plus ~2,000 of prologue, against 29,780 — **119 %**. Exactly one NMI lost, and never
two since 35,400 < 2×29,780. That is precisely the data: 17 loads, 17 lag frames, one each.

**Irreducible, with margin.** The overrun is ~5,600 cycles. `InitializeMemory`'s Y argument is the
only parameter, is a compile-time constant, and only shortens page 7 — max saving 1,368. The
prologue varies a few hundred through `SoundEngine`. The sprite-0 busy-waits are already skipped
(`ChgAreaMode` clears `Sprite0HitDetectFlag`). Nothing is input-, position-, RNG- or route-dependent,
which is exactly what the data shows: lag at ITC phases 0-19, every level, both entry modes. F264.

**Learned.** The standing prior ("the lag *is* the load, so probably irreducible") was right about
the conclusion and wrong about the reason, and the reason is what a future session would have built
on. Second time today that a documented attribution was solved one routine away from the binding
one — F210/F216 solved `HeadChk`'s guard instead of `PlayerBGCollision`'s, and §1 blamed the
routine that renders the screen instead of the one that clears RAM. **When a doc attributes a cost,
check the cost, not the story.**

**Next.** The board is now five items: L1 and L2 running (both at their controls, no banked frames),
L3 (8-4 room 3's approach, corrected form) and L4 (8-4 room 2's exit pipe, subpixel key) un-run, L6
folds into L2. Both un-run items are in 8-4, the only level where one frame is the record.

## 2026-08-25 — Session 21 (Linux): L7 — 8-4's first corner search, and the lens the sweep never had

**Context: a memory-bound session.** Five searches were already in flight — three E7 archives on
the Linux box (~2 h left) and two E9b archives on the Mac (~3.5 h) — leaving 2.5 GB spare on a
15 GB box. So the unit had to be one that is mostly *thought and tooling*, with a small tail of
compute. L7 is exactly that shape.

**Did.** Two gaps on the board's L7 row, and the second turned out to be the interesting one.

**(1) 8-4 had never been swept.** `build/explore --anomaly` — the P3.4 corner search, which reports
the first occurrence of each (class, value) pair the WR's own line through the same region never
produces — was run once, on 1-1, 1-2, 4-1, 4-2, 8-2 and 8-3. **Never on 8-4**, in any of its five
sub-areas: the only unquantized level, the one place a single anomalous frame *is* the record, had
had no corner search at all. Mapped its five sub-areas to core frames from the WR dump (F265):
control at 15224 / 15918 / 16355 / 16720 / 17590, each exactly 122 frames after its load — and
those five loads are exactly F264's last five lag frames, which is the independent check that the
map is right.

**(2) No sweep had ever carried an object-slot lens — and the blind spot was the exact shape of the
mechanism we priced at 857 frames.** The nearest class was 5, `Enemy_ID out of table`:

```c
for(int q=0;q<5;q++) if(r[ENID+q]>0x36){ ... }
```

`Enemy_ID` is `$16-$1b` and `Enemy_Flag` `$0f-$14` — **six** slots (F261) — so slot 5 was never
looked at; and `StarFlagObject` is **`$31`, below `$36`**, so a second star flag in *any* slot could
never have fired it. F258 measured that mechanism at 857 frames and F262 closed the write path to
it; but the one class a sweep would have needed to *see* it was the one class the sweep did not
have. Added class 17 (`Enemy_ID` novel in a **live** slot — calibrated against every id the
reference line parks in any slot, live or stale, so a stale byte cannot masquerade as novel) and
class 18 (**a second** `StarFlagObject` — calibrated by *count*, since the end-of-level castle
legitimately parks one), and widened class 5 to all six slots. F266.

**Controlled, then launched.** 45 s on the Bowser room: the calibrator reports 6 normal `Enemy_ID`
values, the seeded WR line reproduces the ending exactly (`GOAL victory=17865 last_input=17846`,
WR 17846), and neither new class fires on 3,393 rollouts — the expected null. `r5` is running now at
`--cells 40000` under `MemoryMax=800M` (the RAM there was); `r1`-`r4` are queued behind a detached
`WAIT=1 WAITN=1` waiter that fires them at 80,000 cells when the E7 archives exit.

**A side effect worth naming.** The Bowser-room root is the only sweep root whose horizon reaches
the end of the game, so its default goal (`OperMode 2 && World >= 7`) is live: any `best_*.path`
with `last_input < 17846` is a record on the ending-input coast. That makes `r5` a free H1 probe,
and it sits in the room where H17 (suppress Bowser for a faster axe) lives too.

**Also fixed:** `tools/build_explore.sh` builds to a temp file and `mv`s it into place. Rebuilding
`build/explore` while five searches have it mapped would otherwise either fail with ETXTBSY or
disturb a job in flight; a rename is atomic and leaves the running inode alone.

**Learned.** A sweep's verdict is only as wide as its predicates, and ours had been read as
"the novelty search found only mundane hits" when what it actually said was "found only mundane
hits *among ids above `$36` in five of six slots*". The negative was never wrong; it was narrower
than the sentence people (we) carried forward. Same failure mode as F210/F216 and the `timing-model`
attribution the day before: **check what the evidence covers, not the summary of it.**

**Next.** Read the sweep out when the five jobs finish (`grep ANOMALY runs/L7-w84/*.log`, replay
each hit, verdict per sub-area). Then the cheap follow-up F266 opens: re-run E6's six roots with the
object lens, because 1-1 / 1-2 / 4-1 / 4-2 / 8-2 / 8-3 have never been looked at through it either.

## 2026-08-25 — Session 21 (Linux, cont.): L4 — the first search ever aimed at 8-4 room 2's pipe

**Did.** Took the second un-run board item, since it fits the same budget: a launcher, a 40 s
control, and one small job. L4 is 15 priced frames at 8-4 room 2's exit pipe (F245: 23 off-cap
frames at cols 150-151, speed 38 → 23 against the block stack at c152/c153). Two things had kept it
looking closed and neither survives reading:

- **MrWint's `W84Part2VertPipeEntry` proves 40 frames optimal and the WR matches it** — *from
  x 2373*. That segment fixes the state at x 2373 by construction; the 15 frames lie inside exactly
  that given. H39's seam corollary, again: the approach chooses the state the proof assumes.
- **No 8-4 search has ever keyed subpixels**, and F245/F247 put these windows at 1-2 px. E9b learned
  that lesson in 1-2 in session 19; this is the same defect one level over.

**The goal question, taken seriously.** Session 18 produced three fake records from proxy goals
(F230/F237), so the argument is written down before the search runs (F267): goal =
`GameEngineSubroutine == 3` (pipe entry), baseline **16182** = the WR's own; monotone with the
record because 8-4 is unquantized and an area load costs a constant 122 frames with exactly one lag
frame at every ITC phase (F264/F265) — so entering the **correct** pipe k frames earlier reaches the
axe k frames earlier. And the caveat is not hypothetical: the 40 s control itself produced a
wrong-pipe rollout (`AreaPointer = 229`, a 255 px position jump at frame 16223, x 1536) that
satisfies the goal and is worth nothing. Every candidate gets a core replay and a destination check.

**Control green:** `GOAL frame=16182 (baseline 16182, +0)` — the seeded WR line reproduces its own
entry to the frame, 9,658 rollouts / 2 goals / 0 deaths in 40 s, so the goal is reachable by the
rollout policy rather than a needle.

**Running:** root `a` (16050, the 132-frame approach) at 40,000 cells under `MemoryMax=700M`. Root
`w` (15905, the whole room, which lets the approach *state* vary rather than just the arc) is
written and deliberately not launched — the box was holding 7.2 GB of E7 archives.

**Memory accounting for the next session** (this was the binding constraint all session): E7's
three archives are 2.58 + 2.59 + 2.03 GB and exit within ~2 h; L7's `r5` is 0.53 GB, L4's `a` 0.53
GB, and L7's queued `r1`-`r4` are 1.2 GB each when they fire. The L7 waiter was restarted with
`WAITN=2` once L4 started, or it would have waited for `a` and `r5` to finish instead of for E7.

**Next.** When E7 exits: `CELLS=150000 MEMMAX=2500M ./runs/L4-w84r2/launch.sh` (both roots at full
size). Then read out L7's five sweeps. The board's remaining un-run item after that is **L3**
(8-4 room 3's approach, 38 frames), which is an engine/`bfscx` unit, not a Track E one.

## 2026-08-25 — Session 21 (Linux, cont.): H12 — the first over-cap displacement, and the wall it hits

**Context.** The user asked, mid-session, whether ROM reading was a dead end given that session 20
read the ROM end to end. It is not the same ground: **E10 asked what can *write* where** (arming ACE,
corrupting state) and closed that. H12 asks what the *inputs mean*, and it is on the board as a
structural long shot. `docs/input-semantics.md` (P0.7) had catalogued the ordinary paths and stopped
at "L+R sets facing = 3, which doubles the friction adder" — it never asked what else reads
`PlayerFacingDir`, and **3 is a value no single button can produce**.

**Did — the find.** `PutPlayerOnVine`'s `SetVXPl` (smbdis 12219) positions the player on any grabbed
climbable metatile with `ldy PlayerFacingDir / adc ClimbXPosAdder-1,y`, and — when the cell is
buffer-1 column 0 — `adc ClimbPLocAdder-1,y` onto `ScreenRight_PageLoc`. **Both tables are 2 bytes.**
Confirmed in the ROM image, not just the listing: `f9 07 ff 00 18 22 50 68 90` occurs exactly once, at
CPU $DE25. So facing 3 reads **$ff** for X and **$18** for the page: `+24 pages = +6,144 px`. The
flagpole path stores facing = 1 first; **the vine path does not**.

**Measured on the core, with controls** (`tools/climb_facing_probe.py`, one command). WR + L+R forced
from 1-1 frame 1226, a `$26` metatile poked into the block-buffer row the side probe reads, grab at
frame 1251 where the probe lands in buffer-1 column 0:

| facing | page | X | x | |
|---|---|---|---|---|
| 1 (control) | 11 | 249 | 3065 | = `$f9`/`$ff`, in-table |
| 2 (control) | 12 | 7 | 3079 | = `$07`/`$00`, in-table |
| **3 (L+R)** | **36** | **255** | **9471** | out of table — **+6,406 px in one frame** |

That is the first over-cap forward displacement this project has produced. H47's premise — "every x
bound prices progress at the running cap" — has a counterexample.

**And the wall.** Frame 1252 puts him at x 2954, *behind* where he started. `ChkPOffscr`/`KeepOnscr`
(5428) runs every frame: `GetXOffscreenBits` for the player, then snap to `ScreenLeft` if d7 or
`ScreenRight − 16` if d5. A page-scale jump always reports d7, so it always snaps left — **−111 px net,
about 44 frames lost.** The general form is the useful part: *any* horizontal teleport large enough to
set an offscreen bit is undone in the direction the bits report, so a displacement can only pay if it
lands **inside the current screen**. F269.

**The number that makes this session worth it.** If the clamp bounds displacement to the screen, how
much screen is there? The furthest right the game permits is `ScreenRight_X_Pos − 16`. Against the
WR's own position, over every control frame: **median 127 px in every level measured** (1-1, 1-2, 4-1,
8-2, 8-4 rooms 1 and 5; minimum 42). HappyLee runs a constant **127 px ≈ 50 frames** behind the
maximum legal on-screen x. That is the ceiling on the whole H47 class, it is far more generous than
anyone assumed, and it means a mechanism does not need to be exotic — it only needs to land in the
screen. F270.

**And one such mechanism already exists.** `ClimbingSub` writes `PlayerFacingDir := L/R EOR $03`, so
L+R **on a vine** sets facing = **0**, which indexes `ClimbXPosAdder-1` = `$8a`. With any column but
buffer-1 column 0 the page is untouched, so no offscreen bit and no clamp: measured at 1-1 frame 427,
**x 583 → 714, +131 px, unclamped**. It is not yet a saving — the placement is absolute
(`column*16 + $8a`, wrapping inside the page), so the next frame's grab re-placed him, and arming
facing 0 needs a vine, which exists in 1-2 and 4-2 but **not in 8-4, the level where one frame is the
record**.

**Learned.** The negative that had been carried forward — "no over-cap displacement mechanism has ever
turned up" — was true only of the places anyone had looked, and nobody had looked at what the *inputs*
index. Same shape as F266 earlier today (the sweep's blind spot) and F264 the day before (the
misattributed lag frame): **the evidence was narrower than the sentence summarising it.**

**Also corrected:** `input-semantics.md` §4 skipped swimming because "no water on the WR route". 8-4's
water room is **696 route frames**, 667 of them at the swim cap. The one place the route swims has
never had its input semantics read — that is now the top H12 leftover.

**Next.** (i) Read the swim path. (ii) The other eight `ldy PlayerFacingDir` / `Player_MovingDir`
readers — facing 3 and 0 are out of range at every one of them and only `SetVXPl` has been checked.
(iii) Re-price mechanism hunts against F270's 127 px rather than against "beat the cap".

## 2026-08-25 — Session 21 (Linux, cont.): L3 reopened — the negatives were blind by construction

**Did.** The board called L3 "un-run". It wasn't: F133(d)/(e) ran it twice — diversity beams that kept
2,303 then 4,333 apex candidates, with exhaustive continuations that died at layer 188, **byte-identically**.
I said the wrong thing to the user earlier off the stale board row; the fact underneath said otherwise.

**Then the byte-identical death started to look like a symptom rather than convergence.** Two runs, one 5×
wider than the other with an extra axis, dying at the same layer with the same max x, is not independent
evidence — it is the same systematic omission twice.

**Found it.** The room reduces to: *is a 33-cost end class reachable at step ≤ 161?* Nobody had ever asked
what those classes **are**. Added `SMBOPT_DUMP_ENDCLASSES=1` and looked:

```
ENDCLASS R=33 n=1280  x_spd 1.00..10.98 px/frame  abs [0..0]  ground 1280 air 0  running 1280 walking 0
```

All 1,280 cheapest classes are **on the ground, running, `x_spd_abs` = 0, moving right at 4.8–11 px/frame,
facing LEFT** — a **landing frame** (abs stale because `ImposeFriction` doesn't run airborne without L/R,
and the collision sets `Player_State = 0` after the movement subs).

**And the beam key cannot represent that.** The class is
`(x_spd, x_spd_abs, moving_dir, facing_dir, is_on_ground, running_speed)`; the key was
`off,y,spd,sub,vf` — **four of the six fields absent**. F133(d) had explicitly argued the beam was sound
because "the return cost is a function of the bucketed variables". It isn't. States with the same speed
band and y but different return costs competed for one slot, ranked by `h`, which prefers the **faster**
state — the exact opposite of the R=33 profile. Widening 5× just made the same blind spot bigger.

**F133's measurements stand. Its soundness argument does not** — and that argument was the reason the room
was treated as closed. H25 is reopened (F272).

**Fixed and running.** New `--beam-buckets` axis `cls` = `(x_spd_abs, moving_dir, facing_dir, is_on_ground,
running_speed)`. Engine control gate byte-identical after the change. Phase 1 (approach to step 162, beam
250, 2,180 buckets against the old key's far smaller count) is running on the now-empty Linux box; phase 2
is the exhaustive continuation from 162 to deadline 194, and a goal there is H25's frame.

**Learned — the third time today.** F266: the sweep's predicate couldn't see the class that mattered.
F264: the lag frame was attributed to the wrong routine. Now F272: the beam key couldn't represent the
state that carries the cheapest return. **Every one was a negative whose *scope* was narrower than the
sentence recording it.** When a search says "dry", the question to ask is not "how wide was it" but "could
its key have held the answer at all".

**Also this session:** the swim section closed one unit short of 259 frames (F271); H12's out-of-table vine
teleport measured and clamped (F268/F269) with H47 priced at 127 px ≈ 50 frames (F270); L7's sweeps moved
to the Mac; and my own L7 Mac watchdog killed the two E9b archives mid-run (relaunched, incident recorded
in STATUS — a watchdog must only kill PIDs it started).

**Late addendum (same session): L2 is dry.** The three 1-2 archives finished while L3 was being built —
`sub16` 8.59M rollouts / 206M frames / 223 goals, `sub32` 10.13M / 243M / 340, `body` 8.43M / 232M / 96 —
**all three sitting exactly at the control (`best=3764` vs baseline 3763), zero banked frames** against a
deficit of 8, after ~680M simulated frames. That is the round run *after* the subpixel-key defect was
fixed, so it is the informative one. F273; board row updated. The live board is now: **L1 running (Mac),
L3 running (Linux, the reopened one), L4 stopped pending a full-size relaunch, L7 queued (Mac), L2 dry.**

## 2026-08-25 — session 22 (Linux). L3 finished and is dry; L4 was reporting fake records and is fixed

**Session shape:** the prompt was "see what's in progress, arm watchers, handle anything that finishes",
so this is a caretaking session — no new unit was opened. Two of the three live jobs reached a state that
needed acting on, and one of them turned out to be broken in a way that mattered.

**Did.**
1. **L3 / H25 phase 1 had just finished** (5,225 apex candidates at step 162, 1640.8 s). Wrote
   `runs/L3-w84r3/launch_phase2.sh` — the resume command STATUS had checkpointed, wrapped in
   `systemd-run MemoryMax=10G MemorySwapMax=0` + `tools/watchdog.sh`, because the checkpointed command
   carried no cgroup cap and the standing rule has no exception for short runs. **Phase 2 came back dry
   in 11.9 s:** frontier bound-pruned to zero at layer 188, no goal (F275).
2. **Checked whether the `cls` fix actually bit**, since that is the whole reason the unit was reopened.
   It did: the continuation's layer counts differ from both earlier negatives (layer 185: 151,752 vs
   F133(e)'s 151,546 and F133(d)'s 86,322) while `max x` per layer is identical and all three collapse at
   exactly layer 188. A genuinely different candidate set reaches the same wall. Also dumped the bound's
   end-class census to pin the target: R=33, n=1280, all ground / running / `abs 0`, moving RIGHT at
   1.00–10.98 px/frame, facing LEFT — the landing frame F272 predicted.
3. **Relaunched L4 at full size** (`CELLS=150000 MEMMAX=2500M`, both roots) now that L3 had freed the box —
   STATUS listed this as the first thing to do when RAM frees.
4. **Caught L4 reporting two fake records within ten minutes, and fixed the cause** (F274). See below.
5. **Killed an orphaned machine-wide watchdog on the Mac** (pid 57194, the pre-incident E9b launcher's
   3 GB RSS killer, still scanning every `explore` on the box 4h49m after its own children died). The
   current E9b pair keeps its own watchdog (78958). This is the hazard the last commit flagged.
6. **Armed two watchers**: the L4 logs for goals and terminal states, and a 5-minute Mac poll that emits
   only on change (E9b best, `done:`, L7 log count, class-17/18 anomaly count, any "AHEAD OF THE WR").

**Learned — the L4 failure is the interesting part of the session.** The full-size `w` root printed
`GOAL frame=16074 (-108)` and `GOAL frame=16070 (-112)`, both flagged `*** AHEAD OF THE WR ***`. Core
replay: entry at **x 2116 (page 8)**, and Mario re-emerges at **x 312, `AreaPointer` still $65** — the
room-2 **loop-back** pipe, dumping him back at the room's start. The launcher had predicted exactly this
and required a destination check, so the false positive itself was anticipated. **What was not anticipated
is the second-order damage:** `ONGOAL` (`explore.c:454`) only records a goal that *improves* on the
incumbent, so banking a 16070 loop-back makes every genuine entry — which cannot be earlier than ~16150 —
permanently unreportable. The run was still printing progress while having lost the ability to answer its
own question. Fixed by ANDing a position clause into the goal (`--goal-ram 0x0e=3,0x6d=9`, i.e. pipe entry
**on page 9**, which the page-8 loop-back cannot satisfy and the WR's own entry does); both roots
relaunched and reproduce `GOAL frame=16182 (+0)` exactly. Evidence preserved in `runs/L4-w84r2/s22_nopage/`.

That is the third time the F230/F237 doctrine has bitten — **a proxy goal makes fake records** — and the
first time the proxy also *suppressed the true ones*. Worth generalising: any search whose goal is a
state predicate rather than a position-qualified one should be audited for the same pattern, because the
incumbent rule turns one false hit into permanent blindness rather than one bad candidate.

**Next.** L4 (both roots, 6 h) and E9b (Mac, ~5 h left) are running; L7's r1–r4 fire when E9b exits.
H25 stays `untested`, not `refuted` — the honest next lever there is phase 1's *width* (`--beam 1000`,
~4x its 27 minutes), not its key, which is now correct.

**Addendum, same session — H25 parked by the user.** Asked whether L3 was dead, the answer was yes on the
evidence: this hypothesis has had each of its three structural objections closed in turn (F125/H39's
apex-goal defect → L3 emitted a set of 5,225 apexes; F272's key defect → the `cls` axis, verified to have
changed the retained set; and what remained was only beam **width**). User's call, and the right one: *"I'm
done widening beams. I'm done just searching further into the abyss."* Parked, not refuted — the distinction
still matters and is written into the hypothesis. What would reopen it is a **different primitive**, not a
bigger search: a backward reachability from the 1,280 already-enumerated R=33 end classes to a step ≤ 161
state, which starts *from* the slow landing states a forward beam deletes. Nobody should build that for one
frame; if it ever exists for another reason, H25 is free. The 19 GB layer dir was deleted (`launch.sh`
regenerates it in 27 min). `P2.2a′` in "Next up" was struck through at the same time — it was a restatement
of the same unit and would otherwise have been picked up by a future session as new work.

**Addendum 2 — F274 audited, not left as a question for the user (F276).** I had ended the previous
exchange by asking whether to audit the other launchers. That was the wrong call: it is my job to know
whether days of agent work produced real results or suppressed them, and "should I check?" is not a
question the user should have to answer. Audited immediately. **The suppression requires the incumbent to
fall below the baseline** — a record is `<= baseline-1`, so it is only unreportable if an earlier goal
already set the bar lower. Swept every `GOAL frame` line in every Track E log on both machines: **all of
them are `baseline+1`**, and E3-w42 found no goal at all. The bar never once dropped below a baseline.
**No record was ever lost.** L4's `w` root today is the only run that ever set a below-baseline incumbent,
caught ten minutes in. The correct pattern also predates the bug — E3-w84 pins page and X-in-page, E3-w42
pins the destination — so L4 was the outlier (newest launcher, only site with multiple unqualified pipes),
not evidence of a systemic defect. L2's dry (F273) and every other Track E negative stand.

**Addendum 3 — the handoff was broken, and it would have stalled the project.** The user asked whether the
E6 object-lens re-run was documented well enough that a fresh agent would actually run it. It was not.
It existed only in prose paragraphs above the "Next up" table — but PROCESS §2 tells a fresh session to
take *the first unblocked item in the table*, and **the table was stale at the top**: `E9b-1` was labelled
"START HERE" while running on the Mac, `E10` was done (session 20), `E11` was answered by F273, and `E9b-2`
was all but answered by the same fact. An agent following the process literally would have re-run finished
work and never reached the object lens at all.

Fixed by making the un-run work into **actual units with IDs, sizes and acceptance criteria** — `L8`
(E6's six roots with the object lens), `L9` (read the L7 sweep out), `L10` (the remaining facing-direction
readers) — placed at the top of the table, with the four stale rows struck through and annotated with what
actually happened to each. The ordering prose above the table was rewritten to match and to say plainly
that the session-19 order is stale.

**L10 is deliberately first**, and the reason generalises: it is pure ROM reading, so it is the only unit
that is *unblocked while the machines are full*, which is the project's normal state. Every other unit
waits on RAM. A queue whose top item is always RAM-blocked silently converts a full box into an idle
session — and reading is what has actually produced this project's finds (F268 came from reading, not from
809 M simulated frames).

**Lesson worth keeping: prose is not a queue.** Three separate things this session were "documented" in the
sense that a human could find them, and would not have been picked up by the documented decision procedure:
the E6 re-run, L7's read-out, and the fact that `r5` had been stopped at 25 %. Anything that must happen
next belongs in the table with an ID, or it does not exist.

## 2026-08-25 — session 22, unit L10 (user-directed): the other nine facing/moving-dir readers

**Did.** Read all nine un-audited `PlayerFacingDir` / `Player_MovingDir` sites (smbdis 5989, 6152, 6184,
6208, 6346, 6396, 9479, 12079, 14612) against the real table sizes in the listing, and followed the two
propagation chains they opened. Pure reading, run with four search jobs live — which is exactly the point
of having a reading unit at the top of the queue.

**Learned.**
1. **The vine is still the only reader that goes past its table into something that moves Mario** (F277).
   Most sites were never index sites at all — 6152/6184 only `cmp`, 6396 tests d0 with `lsr` so 3 acts as 1,
   12079 tests with `dey/bne`, 14612 uses `and` for a graphics offset. `ClimbAdderLow`/`High` at 5989 turn
   out to be **4 bytes each**, sized for exactly the 0–3 index, so facing 3 is covered by construction.
2. **One genuine second out-of-table read: `FireballXSpdData[2]`** (6346) — a 2-byte table indexed by
   facing−1. Real, but it lands only in `Fireball_X_Speed` and needs Fiery Mario, which this route never
   takes. Recorded rather than chased.
3. **A new primitive, found and closed in the same unit (F278).** `ProcSkid` (6217) is the only writer in
   the game that can put a **3** into `Player_MovingDir`. That state cancels *both* known L+R penalties at
   once — `X_Physics` keeps the path to the 40 cap, and `GetXPhy` skips the friction doubling — which was
   genuinely surprising and looked for a moment like the lever. It is not: the same writer zeroes
   `Player_X_Speed`, and `SetMoveDir` overwrites the direction on any non-zero speed, so it is **one frame
   of favourable branches bought with the player's entire horizontal speed**. Code-level negative, no search
   needed, which is the kind of closure PROCESS actually wants.
4. **A live constraint fell out for L4** (F279): a downward pipe needs `PlayerFacingDir == 1` **exactly**
   (12079), so L+R blocks pipe entry — worth checking the model honours it, since L4 is searching a pipe
   entry right now. And `ImpedePlayerMove` sanitises `$00` = 3 to the `$00` = 2 path via `ldx #$02`, so the
   F278 state cannot corrupt the clip programme's own routine.

**Next.** L10 is struck from the queue; the top unblocked units are now **L9** (read the L7 sweep out when
its roots finish) and **L8** (E6's six roots with the object lens, when RAM frees). Four jobs still running
on Linux, two on the Mac.

**Correction, same session — F279 was mis-scoped and is fixed.** I recorded "a downward pipe needs
`PlayerFacingDir == 1`, so L+R blocks pipe entry" and handed it to L4 as a constraint to check. Checking
it is what showed it was wrong. There are **two** pipe mechanisms and I conflated them: 12079 (`ChkPBtm`)
is the *side*-collision handler for the `$6c` and `$1f` bottom-pipe metatiles, and that is what gates on
facing. The **vertical** pipe entry — `HandlePipeEntry` (12270), the one that sets `GameEngineSubroutine
= 3`, which is **L4's actual goal** — has **no facing check at all**; it needs Down held plus both foot
metatiles ($11 right, $10 left).

L/R does block a vertical pipe, but through a different mechanism: the Down-nullification at smbdis 5584
zeroes *both* `Left_Right_Buttons` and `Up_Down_Buttons` when Down is pressed while grounded with any
left/right held, so the Down test fails. Airborne, it is skipped. **And `smb-opt` already encodes exactly
that** — `emu.rs:523` guards the entry with `(!started_on_ground || joypad_lr.is_empty())`, the same
disjunction the ROM produces. So there was **no model gap and nothing for L4 to fix**, and L4 runs the
real core regardless.

Caught because the follow-up was actually done instead of left as a note. The surviving rule is the
practical one, for the right reason: grounded, a vertical pipe needs Down with no left/right held.

**Session 22, later — 8-2 closed, the Mac fixed, and the 1-2 clip re-opened as L11.**

**L1 / 8-2 is DRY (F280).** Both Mac archives ran the full 21,600 s and printed `done:` at `best=12953`
against baseline 12952 — one frame *worse* than the WR, zero banked, across **~903M frames**, with
`anom=0x00000` in both. `maxx` 3471/3463 against the 3283 threshold, so the frontier did reach past the
wall; it never got there cheaper. That was the largest priced target left (114 frames). **Board down to
two threads: L4 and L7.**

**The Mac was doing two slots of provably useless work (F281).** When the waiter fired, `launch_mac.sh`
silently ignored the `SKIP='r3 r5'` it was given — the Linux launcher has had ONLY/SKIP since it was
written and the Mac one never did — so it launched all five roots, including r3/r5 at the same `--cells`
**and the same seeds** as the pair already running here. Same binary (F248 byte-identity) + same params +
same seed = byte-identical rollouts. Caught by reading the launcher, not the logs; the logs looked
perfectly healthy. Killed the duplicates, added ONLY/SKIP plus a `SEEDADD` offset to the Mac launcher,
and relaunched them as `r3s100`/`r5s100` at seeds 183/185 — independent coverage instead of a duplicate.
**Second instance this session of two launchers for one job drifting apart** (the first was the CELLS
60000/80000 split). Standing rule added: when a job moves machines, diff the launchers before trusting a
number. Both failures were silent under-delivery, never an error.

**Then the user's own question — the 1-2 pipe clip — turned out to have the best remaining answer on the
board, and it was not queued.** Chasing the slowdown mechanism end to end: `ImpedePlayerMove` (12318) is
the only routine that kills horizontal speed on terrain contact, both the side and bottom paths funnel
into it, and it zeroes `Player_X_Speed` while leaving `Player_XSpeedAbsolute` and `Player_X_MoveForce`
alone. `SideCollisionTimer` has exactly one reader (`ScrollHandler`, 5388) and gates **scrolling**, not
acceleration. The escape hatch is F244's sink: feet into a solid cell with `Y & $0F < 5` takes `LandPlyr`
instead, which zeroes only *vertical* speed and skips the side check for that frame.

A promising-looking side finding died on inspection: the jump-arc class **and** the airborne speed cap are
both selected from `Player_XSpeedAbsolute`, which freezes whenever Mario is airborne with no L/R held
(`ImposeFriction` runs unconditionally on the ground but only `if Left_Right_Buttons` in the air), and
`PlayerPhysicsSub` reads it *before* the frame's `ImposeFriction` can refresh it — so jump power is
genuinely decoupled from actual speed. **But `smb-opt` already models this exactly** (`emu.rs` 307 /
317 / 323 mirror the ROM), so every search that went dry already had it available. Not a new lever.

**The real answer is F144/F145, and it inverts the premise.** The clip is not costing time — **it is
already gaining 3 real, core-verified frames** (77 vs 80, 0 mismatches, and the arrival strictly dominates
the WR's). **The scroll refunds them:** `ScrollLockObject_Warp` arms `WarpZoneControl = 4` on
`ScreenLeft_X_Pos` reaching 2816, which is a function of where Mario has *been*. Arrive early and the
scroll is left behind — at step 1217 we are at the WR's step-1220 x with more speed and height but
`ScreenLeft` 2806 vs 2809, and the warp is then dry at 60. **In 1-2 a frame banked before the warp zone is
a frame lent to the scroll.** The residue is named exactly in F145: 2,016,915 goal transitions reach the
post-clip milestone at layer 77 and **only the auto-pick and its scroll-maximal parent were ever
followed**. The experiment is a **goal-function change, not more search** — rank on `ScreenLeft` through
the clip (`offset-census --sl` already exists) instead of gating on position and checking scroll after.
And F145 re-prices Maru's 3 frames onto exactly this spot: they cannot be anywhere else in the level.

**Queued as L11 at the top of Next up.** It had been sitting in two facts for days without ever becoming
a unit — the third instance this session of "prose is not a queue", and the most expensive one, because
this is the only experiment left anywhere that changes the goal function rather than adding search.

**Session 22, close of 1-2 — the user's push is what did it.** I had recorded the Maru370 figure with an
S-fact hedge ("a claim to verify"), and the user pushed back: that number is a published, widely-cited
result, not somebody's story. He was right, and the hedge was doing real damage — **believing the number
is exactly what closes the level.**

Followed through: 1-2 needs **8** frames to cross its framerule, and a partial saving in a quantized level
pays **zero**. F145 (ours, verified) proves everything except the wall clip already optimal — intro free by
construction, opening at MrWint's own optimum, ~1050 frames x-optimal, pit optimal, two later segments
optimal. F144 (ours, verified) puts the clip's ceiling at **3** via an *exhaustive* rung — layer 77 against
the WR's 80, so 3 is minimal from that root, not a lucky find. And Maru370's hand-made "perfect 1-2",
with **no search tool at all**, lands on the same 3 and sits 5 from the framerule against HappyLee's 8.
Two independent routes to the same ceiling. **3 < 8, so 1-2 cannot cross its framerule**, and the 3 banked
frames are provably worthless because the very fact that bounds the level (F145) also proves nothing else
in it can supply the other 5.

So **L11 was queued and closed unstarted inside the same session** — an hour between the two. That is not
churn: queueing it was right on what was known then (a named, never-run residue with outside evidence),
and closing it was right once the arithmetic was actually done. The lesson is that the arithmetic was
always available and nobody had done it; the level had been sitting at "dry, rollout-policy negative"
when it could have been sitting at "shut by counting". **A closure by counting is worth more than a
closure by searching**, and it costs a fraction as much.

H22 moved `untested` -> **refuted** with F144+F145 as the proof artifact rather than a search record,
which is exactly the kind of evidence PROCESS asks for. The route's per-level picture is now: 1-1 closed
(F124), 4-1/8-1/8-3 zero available loss (F225), 4-2 measured closed both routes, 8-2 dry (F280),
**1-2 closed by arithmetic (F283)** — and **8-4 is the only level left**, which is where both surviving
threads (L4, L7) already live.

## 2026-08-26 08:45 — session 22 ends: the board is empty, and the seeds converged

**The last three roots finished at 07:33** — `r1s200` 268.88M frames, `r2s200` 259.85M, `r4s200` 242.85M,
all goals 0. `pgrep -x explore` is empty on both machines. **The project has no running compute and no
live thread for the first time since session 17.**

**L7's final number: ~3.25 billion simulated frames**, all ten roots, all five of 8-4's sub-areas, two
independent seeds each, carrying F266's object-slot lens that no earlier sweep in this project ever had.
**Class 17 and class 18 never fired once.** Every class that did fire was run down rather than waved at:
`GES` 6/11 are `PlayerLoseLife`/`PlayerDeath` (the ~4.5M deaths), the position-jump and `AreaPointer 229`
hits are the room-2 loop-back pipe we already knew, the frenzy classes are the game's **own** `AreaFrenzy`
spawner (core-replayed), and `DuplicateObj_Offset` is firebar/Bowser slot duplication.

**The best evidence in the whole unit is something I did not plan for: the independent seeds converged.**
`r1s200` reproduced `r1`'s anomaly mask **exactly** (`0x15002`) and `r2s200` reproduced `r2`'s exactly
(`0x17042`) — different seeds, different machine. `r4s200` differs from `r4` by one bit, and that bit is
the loop-back teleport we already had. Two independent samples returning the same class inventory is
evidence the sweep **saturated** those roots' reachable classes rather than missing by luck. It is still a
statement about this rollout policy and these ten roots — not a proof about 8-4 — but it is a materially
better negative than a single dry run, and it is the right note to end the compute on.

**H1 closed out negative too**, from the only roots whose horizon reaches the axe: `best_last_input=17846`,
exactly the WR's own, over 468M frames. That is the first direct test of the approach F223 explicitly left
untested.

**How the whole board closed, in one line each:** L7 dry (F285/F286), L4 dry (F284), L1 dry (F280), 1-2
closed by arithmetic (F283), L3 parked (F275), L10 done (F277–F279), L11 closed unstarted (F283).

**What I am careful NOT to write down:** that the record is unbeatable. Every priced target has been
searched where it was priced, and the unbounded thread has been swept — but H47's class (an over-cap
displacement mechanism, priced at up to 127 px ≈ 50 frames, F270) has exactly one known instance and it is
clamped away. Per this project's founding rule that is **un-enumerated, not refuted**, and it is a
mechanism-discovery problem rather than a search problem. STATUS says so explicitly so that a future
session does not inherit a false closure.

**Ops lessons this session cost real search time to learn**, all now standing rules in STATUS: never start
a search without a memory cap; a watchdog must only ever kill PIDs it started; when a job moves machines,
diff the two launchers first (it bit twice in one day — a silent 25 % under-size, then a silently ignored
`SKIP` that spent two slots on byte-identical duplicates); a goal predicate must be position-qualified
wherever more than one site can satisfy it, because the improve-only incumbent turns one false hit into
permanent silent blindness; and **prose is not a queue** — three separate pieces of real work this session
were "documented" somewhere a human could find them and would never have been picked up by the documented
decision procedure.

## 2026-08-26 — project wound down

**Machines released.** Linux: `pgrep -x explore` and `pgrep -x smb-opt` both empty, monitors stopped.
Mac: killed two L7 watchdog shells, one E9b watchdog shell, and both `caffeinate` processes, then
deleted `~/code/smb` entirely. Its other 23 projects are untouched, and no Docker container or image
belonged to this project. Total cloud spend across the whole project: **$0**.

**Disk: 117.2 GB reclaimed, and the narrowing mattered.** `runs/` was 117 GB of which the evidence was
115 MB. The obvious command — delete `*.bin` — would have destroyed **1,522 non-layer `.bin` files**
(2.2 GB of `chain_*.bin` reconstructed input chains, `apex_candidates_*.bin`, difftest inputs), which
are artifacts, not intermediates. Checking the filenames first narrowed it to `layer_*.bin` /
`layer_*.bin.xz` (679 files, 117.2 GB) plus `bfscx_layers/`. All 522 logs, 653 path files and every
non-layer `.bin` survive. Repo went 121 GB → 3.5 GB; free space 147 GB → 211 GB.

**The Mac's logs were pulled back before the delete.** F285/F286 cite `runs/L7-w84/*.log` "on both
machines", and five of the ten sweep roots (`r1`, `r2`, `r4`, `r3s100`, `r5s100`) existed *only* on the
Mac because `runs/` is gitignored. 80 logs and 84 path files are now at `runs/mac-archive/`. Deleting
first would have silently destroyed half the evidence for the project's final result. Checked
`explore.c` too — byte-identical sha256 on both machines, so no engine work was stranded there.

**The engine work is extracted to its own repo:** `~/Documents/smb-opt-modes`, committed and clean.
The 5,921-line patch against MrWint/smb-opt at pin `daa44287` (5 new source files, ~30 modified),
plus `regen_patch.sh`, `Dockerfile.smbopt`, `mac_sync_engine.sh`, `mac_run.sh`, and a README covering
what it adds, how to apply and build it, and the control gate. **Not yet pushed — `gh` is not
installed on this box**, so the GitHub remote has to be created by hand; the one command to finish it
is in STATUS.

The patch was regenerated before extraction and came out **byte-identical**, which is the check that
matters: `regen_patch.sh` refuses if the clone's HEAD has moved off the pin, because a commit in the
clone makes `git diff` return empty and produces a patch that silently applies nothing.

**Final word on the result, stated the way the project's own rules require.** No faster route was
found. Every priced target was searched where it was priced and returned empty; the one thread whose
payoff was not bounded by the loss map was swept across all five of 8-4's sub-areas on two independent
seeds at ~3.25 billion frames, and those seeds converged bit-for-bit on the same anomaly inventory.
**That is not a proof the record is unbeatable.** H47's class — an over-cap forward displacement
mechanism worth up to ~50 frames — has exactly one known instance and it is clamped away. It is
**un-enumerated, not refuted**, and STATUS says so at the top so nobody inherits a false closure.

**Engine repo published.** `gh` installed and authenticated (`mrwatts88`, SSH), and the engine work is
now at **https://github.com/mrwatts88/smb-opt-modes** — private, pushed, tracking `origin/main`.
Private was the default chosen deliberately: it matches `smb1-tas`, and the repo is a derivative of
MrWint's work (it carries only a diff and build tooling, no upstream source). Private → public is a
one-command change; the reverse is not really possible, so the reversible option was taken.

That is the last item. Both repos are pushed and clean, both machines are idle, and the project is
closed.

**Both repos made public** (user's call, 2026-08-26): `smb1-tas` and `smb-opt-modes`. Checked the
committed tree first — **no ROM is in the index** (`roms/` is gitignored and clean). Two committed
files are third-party and are now public: `data/disasm/smbdis.asm` (doppelganger's SMB disassembly —
widely mirrored, but disassembled Nintendo code) and `data/wr/happylee-supermariobros,warped.fm2`
(HappyLee's TAS movie, published on TASVideos). Flagged rather than silently shipped, because removing
them later needs a history rewrite, not just a delete.

**Cleanup second pass.** Asked what untracked files remained, and the answer exposed a miss in the
first pass: `layer_*` did not match the BFS **merge temps**, which are named
`run_<layer>_<thread>_<seq>.bin` and sit in layer dirs' `tmp/` subdirectories — 507 MB in
`bfscx_layers/tmp/` and **2,233 MB in `runs/P2.1b-model/room_layers/tmp/`** across just 31 files.
Those 31 files were **99.5 % of what the first pass had proudly counted as "1,522 non-layer `.bin`
artifacts kept"**; the genuine artifacts (`chain_*`, `apex_candidates_*`, difftest inputs) are
**10.2 MB across 1,491 files**. So the earlier note was right to protect the artifacts and wrong about
their size — the figure was inflated ~220x by temps I had lumped in with them.

Deleted. **Repo: 3.5 GB → 792 MB** (121 GB at the start of the day). Also confirmed: `git status
--untracked-files=all` shows **nothing untracked-but-unignored**, so no stray file was ever left out
of version control by accident; and the ROM is present, gitignored, never in the index, and absent
from all history.

## 2026-08-31/09-01 — Mac session (over ssh to the box): new track RTA-1, "easiest 4-2 for humans"

**Context.** Fresh Mac clone (no engine, core or ROM), Fedora box initially off, then on. Conversation
started as "how would we approach making 4-2 easiest for humans" and ended with a measured answer.
Worked from the Mac driving `~/Documents/smb1-tas` on the box over ssh; the Mac clone holds the docs.

**Reframe.** Not faster (framerule-quantized; humans already reach the TAS's framerule, F36) but wider
input windows: the runner's failure is the wrong-warp mint, not the movement. The user's description of
the failing trick ("slide up the left side of the block facing backwards; works when facing backwards
with legs apart") is a hidden-state question — the kind the core answers exactly.

**Maru's no-L+R TAS** (F3) was the missing artifact: the human-legal optimum with inputs. Found via
TASVideos #6456 → speedrun.com 1wd01 → microstorage; 0 L+R records; replays on the core end to end
(F287). Its 4-2 mints twice, +10 each, with a recipe a human can execute in principle: 1-frame Left tap
on the last ground frame, neutral jump, Right back at contact, run through the freeze facing left (F288).
Facing left = fast-accel for the whole freeze = the amplifier; facing right yields +4–5.

**Perturbation probe** (~30 replays at 1.2 s): jump window 1 frame, tap exactly 1 frame, 9–11 px per mint
by subpixel, total 132 with zero margin (F289). That is the coin flip, quantified. Cheapest fix is one
pixel of margin in mint 1; next unit.

**Corrections made mid-session.** (1) My first pad decoder had the joypad bit order reversed (the game
stores A in bit 7) — caught by cross-checking against the fm2 records before drawing conclusions.
(2) A jump-shift variant group clobbered the Left tap it was meant to keep; re-run corrected
(`tools/rta_mint_probe.py` has the fixed version). (3) I guessed the runner meets (54,7)'s face falling;
the user's description says he goes over the upper pair — so his face is (50,3), rising. Fixed in the
write-up before it became a fact.

**Files.** `data/wr/maru-rtarules.fm2` (third-party, README §Third-party), `tools/rta_mint_trace.py`,
`tools/rta_mint_probe.py`, `docs/experiments/RTA-1-maru-42-mint.md`, F287–F289, STATUS stamp. On the
box, untracked: `data/wr/maru_inputs.bin`, `runs/qn_maru.ram` (both regenerable by the commands in RTA-1 §5).

**Addendum (same session).** The user watched the runner's videos against the map: no early mint (he
goes over the 22–26 bricks, not under), (50,3) mint, then a wall jump on the warp pipe's face — which
the community already caps at "9–10 xpos" and F93 explains. Probed Maru's mint 1 hoping the notch mint
was a forgiving replacement: it is not (1-frame jump window, 2-frame tap, ≤ +10 in every variant; F290).
10 per freeze is structural without L+R, so two-mint lines have zero margin by construction and the
"+1 px" plan is withdrawn. Next unit is the engine mint search for a different mint shape within
Maru's budget (STATUS). `tools/rta_mint_probe.py` gained `--set mint1`.

**Correction (same session, user's catch).** I had listed the warp pipe's face as a candidate for a
> 10 px "tall-face slide" mint — but that face is exactly where the runner's wall jump already mints,
for 9–10. The one measurement of a tall-face contact argues *against* a > 10 shape, and pipe B's top is
unreachable in one jump. Withdrawn in RTA-1 §4, F290 and STATUS. Standing conclusion: no known no-L+R
mint exceeds 10; margin needs a third contact, which costs about a framerule — a trade only the user
can make, so STATUS now leads with that question.

**Unit 2 (same session): the runner's face.** User: no framerule trade, and the failing contact is
the upper pair (50,3), not the pipe wall jump. Built that contact on the core from Maru's prefix
(`tools/rta_503_probe.py`, ~120 replays). It is the *forgiving* one: 3-frame takeoff window, ~7-frame
Right-return window, no subpixel sensitivity (F291). The invisible failures are Left held into the jump
(+0), Right back too early (+8) and a late takeoff (+9); the visible one (no tap, +4) is the only one he
restarts on. Rule set in RTA-1 §3c. Answered the user's comparison: (54,7) and the notch are both
1-frame takeoffs — the runner is already on the best face.

**Unit 3 (same session, user's idea).** "Can we mint by just running off the ledge into the side of
the lower two-block?" Yes: +10, no jump, tap in the last 3 ground frames + 2–4 neutral frames + Right
(F292). Maru's hop is there to avoid exactly that contact (he passes x 788 at y 141, under the face).
This would delete the runner's hardest trick if the floor-level continuation fits the framerule — an
engine comparison (post-mint state → x ≥ 1005, both lines) is the next unit.

**Unit 4 (same session, user's follow-up).** "Why can't we go on top of the three group and rejoin the
old path?" I guessed the lower pair blocked every takeoff; the probe said otherwise: re-jump from
x 812–820 lands cleanly on the group (F293). Cost ≈ 2 frames vs the (50,3) line, hand-crafted. The
line now has no timed jump at a wall. Blocked on one number only the runner's run can give: his slack.
Lesson (again): geometric intuition about SMB1 collision is worth one replay, not a conclusion.
