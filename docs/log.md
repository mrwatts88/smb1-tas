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
