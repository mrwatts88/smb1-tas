# STATUS — SMB1 TAS project

Updated: 2026-08-21 (session 3 — P0.6, P1.1, P2.1a, P0.8 done; P2.1b running; next unit P1.2-lite)
Phase: **P0/P1 → P2** — ground truth mostly done (P0.7, P0.8 remain), stage-1 fast core done
Record to beat: **17,868 frames** (HappyLee, TASVideos #1715M, 4:57.31) — last input on frame 17848 (0-based), then a 19-frame coast to the axe. A new movie must finish the game with an earlier last input.
ROM: verified byte-identical to TASVideos' (W) [!] (`tools/verify_rom.py`); classic-header copy in `roms/` on the Linux box (gitignored) — re-verified 2026-08-21.
Our best full movie: none yet
Host: Linux box (primary). Emulators: FCEUX/BizHawk in the rootless toolbox container `smb1`, Mesen2 native — run via `tools/{fceux,mesen2,bizhawk}_run.sh`, rebuild with `tools/toolbox_setup.sh` (see `docs/experiments/P0.1-tooling.md`). Git: private GitHub remote — commit after every unit, then push (document → STATUS → commit → push)

## Running jobs
- **P2.1b-root1229-par** (Linux box, pid in `runs/P2.1b-root1229-par/stdout.log` header; started 2026-08-21): `build/bfs_par` pole search from the WR's frame-1229 state, 10 workers, 6 GB cap. Check: `tail runs/P2.1b-root1229-par/stdout.log` (one line per layer; ends with `terminals:` / `LAYER FULL` / `no live states left`), `runs/P2.1b-root1229-par/terminals.txt`. A T_set ≤ 1813 = candidate 21-frame improvement (re-verify in FCEUX/BizHawk). Expected ≤ 2 h.

## In progress
- **P2.1b** — 1-1 third room relaxations on the current core. Started 2026-08-21. Part (3) first: `build/bfs` from the WR state at frame 1229 (stairs top, x 3033) with `--deadline 1284 --target-x 3158` (H27 test); then (1) the FPG trigger condition from the code; then (2) the flat-world frontier. Checkpoint: v1 run hit the memory cap at layer 10 (`runs/P2.1b-root1229/`); v2 `src/search/bfs_par.c` (2 KiB states, F50; forked workers) launched as the running job above. FPG geometry written down (F51). Still to do: (2) flat-world frontier; widen roots to 1176/1200; write `docs/experiments/P2.1b-pole-search.md` results.

## Next up (ordered — the top unblocked item is the next unit of work)

| ID | Title | Track | Size | Depends on | Acceptance |
|---|---|---|---|---|---|
| P2.1b | 1-1 third room, sound relaxation on the current core: (1) exact FPG trigger condition from `PlayerBGCollision`/`HandleClimbing`/`FlagpoleRoutine` (x, subpixel, y at the pole); (2) flat-world frontier — point the area/enemy parsers at their terminators, flatten the block buffer, BFS with physics-class + max-P dominance — earliest frame with x ≥ 3158 from the fixed entry (F47); (3) short-horizon search from the WR's stairs-top states for an on-arrival grab (H27) | A | M | P2.1a | Frontier frame with a proof sketch of the relaxation; FPG condition written down; H27 tested |
| P1.2-lite | Build MrWint/smb-opt (rustup nightly-2018 in the `smb1` toolbox, no sudo), run its 1-1 cases, and differential-test its player model against QuickNES on the WR trace (x/y/speed per frame) and on random inputs in the 1-1 third room; port or wrap its XPosHeuristic as the sound bound for P2.1b | A | M | P1.1 | Model matches the core on the WR's 1-1 frames (or the deviations are listed); bound tables available to `bfs_par` |
| P1.2 | Stage-2 core: static recompilation of the SMB1 ROM to C with cycle counting + minimal PPU timing (vblank, sprite-0); or, as a first step, a validated player-physics + BG-collision model with ~32-byte states (P1.2-lite) | A | L | P1.1 | Differential test vs QuickNES on ≥ 10M random frames incl. lag; fps recorded |
| P2.1c | Search engine v2 on the fast core: compact states, multi-process sharding, sound bounds; full 1-1 (all rooms) threshold search for H21 | A | L | P1.2, P2.1b | Ties the WR in 1-1; reports whether T_set − 1 is reachable, with the search record |
| P0.7 | L+R / U+D semantics catalog from the code (all effects, not just the known decel); pause/Select effects on every timer | B | S | P0.5 | `docs/input-semantics.md` |
| P1.1b | Direct-link core: build Nes_Emu into the search binary, use `emulate_skip_frame` (no rendering), measure speedup; keep RAM-identity vs F45 | A | S | P1.1 | ≥ 2× fps over F46 with the same WR RAM trace |
| P2.2 | 8-4 exhaustive search (frame-granular; Bowser RNG, L+R, ending-input trick) | A | L | P2.1 | Report: faster path (verified in two emulators) or proof record |
| P2.3 | Threshold search for framerule N−1 in each flag/pipe level, in remaining-deficit order: 4-2 top route (2), 8-3 with FPG (7), 1-2 (8), 4-1 (9), 8-1 (18), 8-2 (19) | A | L | P2.1, P0.4 | Per-level report |
| P2.4 | Cross-level DP over reachable entry states (RNG / framerule phase) | A | M | P2.2, P2.3 | Best-known full route + proof record |
| P3.1 | Static audit tool: every indexed memory access in the disassembly whose index is player-influenceable; tabulate OOB behaviors. Targets from P0.6 (H7): writes reaching $075F (WorldNumber ≥ 7), $0750/$0751 (AreaPointer/EntrancePage = $65/16), $06D6 (WZC ∈ {2,6} in 1-2) | B | M | P0.6 | `docs/oob-audit.md` |
| P3.2 | RAM oracle: single-byte perturbation sweep per level on the fast core → jackpot map | B | M | P1.1 | `docs/experiments/P3.2-ram-oracle.md` |
| P3.3 | Write-reachability: for each jackpot cell, can any in-game write hit it? | B | L | P3.1, P3.2 | Ledger entries with proof artifacts |
| P3.4 | Fuzzing / Go-Explore novelty search for anomalous states | B | L | P1.2 | Anomalies triaged in the ledger |
| P3.5 | NES Minus World re-examination with oracle + audit (WorldNumber = 36 OOB reads) | B | M | P3.1, P3.2 | Ledger entry with proof artifact |
| P4.1 | Assemble, verify in two emulators, draft submission text | ship | M | a result | User-reviewed before anything is submitted |

## Done
- 2026-08-21 — **P0.8 done**: `docs/prior-tools.md` — the only exhaustive-search tool is MrWint/smb-opt (player-only model, segment searches, 4-4 wall clip); no whole-level/full-state search exists; Maru's best 1-2 is 5 frames from the framerule; F52; H21/H22 annotated; new unit P1.2-lite.
- 2026-08-21 — **P2.1a done**: `src/search/bfs.c` (in-process BFS engine, exact T_set evaluator verified on the WR, deadline pruning); full-state BFS measured infeasible (×5/layer, F49); WR acceleration profile and pole stop decoded (F47/F48); H21 restructured, H27 added; `docs/experiments/P2.1a-bfs-engine.md`.
- 2026-08-21 — **P1.1 done**: libretro QuickNES harness (`src/fastcore/harness.c`, `tools/build_core.sh`, `tools/fm2_to_inputs.py`, `tools/compare_ram.py`) replays the WR with RAM identical to the FCEUX dump on every row (F45, alignment law: FCEUX row r ↔ QuickNES row r−3, input record j → QuickNES frame j−2); 15.0k fps/instance, 104k fps on 12 threads, savestate 12.8 KB / 2.5 µs (F46); `docs/experiments/P1.1-fast-core.md`.
- 2026-08-21 — **P0.6 done**: `docs/warp-model.md` — WZC ∈ {0,1,4,5,6} at any pipe (proof), world 8 only from 4-2's $2F zone, all 58 pipe-destination commands tabulated, completion = axe with WorldNumber ≥ 7, Minus World closed at table level; `tools/warp_tables.py`, `tools/area_data.py`, `tools/ram_trace.py`; facts F38–F44; H5 refuted, H6/H13 refuted at table level, H7 sharpened; `docs/experiments/P0.6-warp-model.md`.
- 2026-08-21 — Research of the current record and community state; plan, process, and status scaffolding written (PLAN.md, PROCESS.md, this file, docs/*). Git initialized, initial commit. See docs/log.md.
- 2026-08-21 — **P0.2 done**: WR movie fetched to `data/wr/`, 17,868 frames confirmed, ROM verified against TASVideos hashes and the movie's romChecksum; `tools/fm2_info.py`, `tools/verify_rom.py`. Facts F1/F15–F17.
- 2026-08-21 — **P0.9 done**: `docs/community-claims.md` — 1-1 known as "1 frame short" since 2009 with no proof; 4-2 top route is 2 frames short (HappyLee); 8-3 FPG/242 = 3 frames; Maru's 8-4 idea; facts F35–F37, H25/H26. Still to mine: thread pp. 1–56/58/61, Maru's movie.
- 2026-08-21 — **P0.5 done**: `docs/timing-model.md` — every WR frame count derived from the code (NMI/timers/boot/loads/flag sequence/pipes/axe); T_set = grab + T + 159; control = load + 154 + w; Start rows 34–43 equivalent; facts F31–F34.
- 2026-08-21 — **P0.4 done**: framerule mechanism verified frame-exactly; slack/deficit per level (1-1 is 1 frame from the next framerule; 1-2 8, 4-1 9, 8-3 10, 4-2 13, 8-1 18, 8-2 19; 8-4 unquantized); `tools/slack_table.py`; facts F27–F30; H21–H24; `docs/experiments/P0.4-slack-table.md`.
- 2026-08-21 — **P0.3 done**: WR syncs in FCEUX and BizHawk/NesHawk with identical per-frame state; axe on fm2 frame 17867 (0-based); 24 lag frames; level-entry frames; `tools/fm2_to_bk2.py`, `tools/check_sync.py`, `tools/compare_dumps.py`, `tools/lua/wr_dump_*.lua`; dumps in `data/wr/`; facts F23–F26; `docs/experiments/P0.3-wr-sync.md`.
- 2026-08-21 — **P0.1 done**: FCEUX 2.6.6 (Lua), Mesen 2.1.1, BizHawk 2.11.1 (NesHawk) all run headless + scripted on the Linux box (toolbox container `smb1` for FCEUX/mono; no host sudo needed); wrappers `tools/*_run.sh`, reproduce with `tools/toolbox_setup.sh`; specs/versions/throughput in facts F18–F22; `docs/experiments/P0.1-tooling.md`.

## Loose ends (small, unassigned)
- (resolved in P1.1, F45) Start-press row: FCEUX applies fm2 record j in dump row j+2, so record 41 acts on row 43; `fm2_info.py` (record index) and the dump (row) were both right.
- The FCEUX/BizHawk dumps and the QuickNES output use different row origins (F45); any tool that mixes them must state the offset. `tools/check_sync.py`/`compare_dumps.py` are FCEUX/BizHawk-only.

## Blocked / Needs user input
- (optional, not blocking) **Native emulator install on the host** would let `tools/fceux_run.sh` skip the container: `sudo dnf install -y fceux xorg-x11-server-Xvfb mono-core mono-devel libgdiplus lsb_release cmake clang gdb strace` (RPM Fusion is already enabled on the host). Everything currently runs in the rootless toolbox container, so this is a convenience only.
- **Cloud**: preferred provider and how to authenticate (a plain VM provider with
  spot/preemptible instances fits CPU-burst search; Railway does not). Needed by P2.

## Key numbers (each must be reproducible by a script in tools/)
| Quantity | Value | Source / script |
|---|---|---|
| WR movie length | 17,868 frames (4:57.31) | `tools/fm2_info.py` (V) |
| WR last input | frame 17848 (0-based); 19 input-free frames follow | `tools/fm2_info.py` (V) |
| WR first Start press | frame 41 (0-based); any Start on rows 34–43 gives the same 1-1 start (F31) | `tools/fm2_info.py`; `docs/timing-model.md` (V) |
| WR Left+Right frames | 85 (U+D: 0) | `tools/fm2_info.py --list-lr` (V) |
| RTA-timing equivalent | 4:54.032 | S |
| RTA-rules (no L+R) TAS | 4:54.265 — 14 frames slower | S |
| Framerule | 21 frames | S |
| WR axe frame (OperMode→2) | fm2 frame 17867 (0-based) = last frame of the movie; timer 317 | `tools/check_sync.py data/wr/fceux_wr.csv data/wr/happylee-supermariobros,warped.fm2` (V) |
| WR level-entry frames (fm2, 0-based) | 1-1 42, 1-2 1944, 4-1 3766, 4-2 6042, 8-1 7723, 8-2 10813, 8-3 12956, 8-4 15057 | `tools/check_sync.py` (rows −1) (V) |
| Per-level slack/deficit (frames) | 1-1 20/**1**, 1-2 13/8, 4-1 12/9, 4-2 8/13 (top route: 2, S), 8-1 3/18, 8-2 2/19, 8-3 11/10 (FPG+242: 7, S), 8-4 unquantized | `tools/slack_table.py data/wr/fceux_wr.ram` (V) |
| Per-level frames (load→next load) | 1-1 1902, 1-2 1870, 4-1 2228, 4-2 1729, 8-1 3042, 8-2 2143, 8-3 2101, 8-4 2810 (+43 boot/title) | `tools/slack_table.py` (V) |
| Lag frames in WR (before the axe) | 24 (7 boot, 1 after Start, 16 area loads; none in-level) | `tools/check_sync.py`, `tools/slack_table.py` (V) |
| 1-1 third room (QuickNES frames) | entry X 2616 speed 0, control after 1045; WR speed 40 by 1079, x 3157.3 at 1280, grab after 1285 (T 370), T_set 1814; sound-bound frontier at the pole: 1272 | `tools/ram_trace.py`, `build/bfs --replay-check` (V) |
| Stage-1 core speed | 15.0k fps/instance, 69k (6) / 104k (12 threads) aggregate; state 12,792 B, save+load 2.5 µs | `tools/build_core.sh` then `./build/harness … --input-skip 2 [--state-every 1]` (V) |
| Emulator alignment | FCEUX row r ↔ QuickNES row r−3; fm2 record j → FCEUX row j+2 / QuickNES frame j−2 | `tools/compare_ram.py … --offset -3 --from 10 --ignore 160-1ff --all` (V) |
| Reachable warp destinations | 1-2 → {4,3,2} or {−1,5,−1}; 4-2 ceiling → 5; 4-2 $2F → {8,7,6}; WZC ∈ {0,1,4,5,6} | `tools/warp_tables.py` + `docs/warp-model.md` §5.4 (V) |
| Ending-input coast length in WR | 19 frames: last A press on frame 17848, axe on 17867 | `tools/fm2_info.py`, `tools/check_sync.py` (V) |

## Spend
Cloud total: $0 / $300 cap.
