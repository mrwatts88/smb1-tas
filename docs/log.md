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
