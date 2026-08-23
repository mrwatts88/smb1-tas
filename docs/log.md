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
Established the billing rules from Hetzner's docs + the authenticated pricing endpoint (F92): hourly rounded up,
monthly cap, ancillary rates — and the one that matters, **a powered-off server still bills; only `delete` stops
the charge**. Measured the engine's scaling limit from run 4's own log (F93): expansion is parallel over
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
(steps 201–221), tight elsewhere (F94). Read the geometry exactly (F92: the pillar is rows 7–9 with an open row 10 — the WR
runs *under* it; pipe B is a floor-to-row-4 wall) and the wall-entry mechanics from the model trace + disassembly (F93: a
Left press turns the foot-check impede into a +1 px push into the wall). Decoded the enemy data: `$3A` at col 46 = **3
goombas on the Y-112 top floor**, the route HappyLee calls 2 frames short — they are not in the model. Added `bfscx
--goal-x PX [--goal-y PY]` (position goals, x-table bound, best-of-layer goal pick; regression control identical),
`tools/bfscx_ladder.sh` (deadline ladder: a position-goal BFS only stays small at the segment optimum — deadline +28
doubled the frontier per layer), `tools/chain_inputs.py`. Segment S1 (root → x ≥ 339, Y ≤ 112): deadline 147 dies at
layer 29; 149 running (~9M states/layer, ~100 s/layer at nice 10, 2 threads, 2 GB cap).
**Learned.** The WR's main-area deficit is two localized costs (entrance fall 10, wall entry 31), so the enemy-free top route
should be ≈ 550–555 — and the thing that can make it 577 is the goomba group, which means 4-2 needs the P2.5-style enemy
module before any proof run is meaningful. The x-only bound's remaining looseness is y-variety (heights), not x.
**Next.** S1 verdict → `bfscx-path … --out` → `tools/chain_inputs.py` → S2 (x ≥ 755, Y ≤ 112) → S3 (x ≥ 1005) → S4 (pipe
entry, case goal) → model length vs 577 → `tools/replay_check.py --case W42Main --first 6584 --prefix 0 --path CHAIN --lift 0
--down` on the core (expect a goomba death) → bound design + the 4-2 goomba port plan. Then the cloud decision.
