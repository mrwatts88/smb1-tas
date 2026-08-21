# STATUS — SMB1 TAS project

Updated: 2026-08-21 (session 2 — P0.1, P0.3, P0.4, P0.5, P0.9 done; P0.6 in progress with checkpoint)
Phase: **P0 — Ground truth**
Record to beat: **17,868 frames** (HappyLee, TASVideos #1715M, 4:57.31) — last input on frame 17848 (0-based), then a 19-frame coast to the axe. A new movie must finish the game with an earlier last input.
ROM: verified byte-identical to TASVideos' (W) [!] (`tools/verify_rom.py`); classic-header copy in `roms/` on the Linux box (gitignored) — re-verified 2026-08-21.
Our best full movie: none yet
Host: Linux box (primary). Emulators: FCEUX/BizHawk in the rootless toolbox container `smb1`, Mesen2 native — run via `tools/{fceux,mesen2,bizhawk}_run.sh`, rebuild with `tools/toolbox_setup.sh` (see `docs/experiments/P0.1-tooling.md`). Git: private GitHub remote — commit after every unit, then push (document → STATUS → commit → push)

## Running jobs
(none)

## In progress
- **P0.6** — Disassembly study #2: warps & area loading → `docs/warp-model.md` (every player-influenceable table index + OOB behavior). Started 2026-08-21. **Checkpoint (resume here):** read so far: `ScrollLockObject_Warp` (WZC = 4/5/6 by world/area type), `WarpZoneObject` (inc WZC when ScrollLock set and Mario Y even), pipe-entry lookup at smbdis.asm ~12288 (index (WZC&3)*4 + pipe by X thresholds $60/$A0; WorldNumber = byte−1; then WorldAddrOffsets/AreaAddrOffsets → AreaPointer). ROM: `WarpZoneNumbers` at $87F2 = 04 03 02 00 | 24 05 24 00 | 08 07 06 00, followed by `GameTextOffsets` 00 00 27 27 46 … → WZC=7 gives WorldNumber 255/255/38 (H5 updated). Dump: 1-2 WZC 0→1→4 (rows 3546, 3721), 4-2 0→6 (row 7608). **To do:** (a) check in the dump (rows 7590–7724: ScrollLock $0723, WZC $06D6, enemy IDs $16–$1B, Player_Y) whether the WarpZoneObject can still fire after the text object in the 8-7-6 zone; (b) read `LoadAreaPointer`, `GetAreaDataAddrs`, `WorldAddrOffsets` (size 8?), `AreaAddrOffsets`, enemy jump table + Bowser-replacement table, warm boot in `Start`; (c) write `docs/warp-model.md`.

## Next up (ordered — the top unblocked item is the next unit of work)

| ID | Title | Track | Size | Depends on | Acceptance |
|---|---|---|---|---|---|
| P0.6 | Disassembly study #2 — warps & area loading: WarpZoneControl + WarpZoneNumbers, pipe index from Mario X, AreaPointer / WorldAddrOffsets / AreaAddrOffsets, EntrancePage / AltEntranceControl, Minus World arithmetic, warm boot ($07FD/$07FF), Bowser-replacement table, object jump tables. Write `docs/warp-model.md` | B | M | — | Every player-influenceable table index is listed with its out-of-bounds behavior |
| P1.1 | Stage-1 fast core: headless libretro QuickNES harness (C/C++ or Rust) with savestate + RAM hash + input injection; benchmark fps/core | A | M | P1.2 | Stage-2 core: static recompilation of the SMB1 ROM to C with cycle counting + minimal PPU timing (vblank, sprite-0) | A | L | P1.1 | Differential test vs Mesen on ≥ 10M random frames incl. lag; fps recorded |
| P0.8 | Survey existing bots/tools (TASVideos thread, GitHub, speedrun.com resources): what exists, which state space each covered, source availability | C | S | — | `docs/prior-tools.md`; hypotheses ledger updated |
| P0.7 | L+R / U+D semantics catalog from the code (all effects, not just the known decel); pause/Select effects on every timer | B | S | P1.2 | Stage-2 core: static recompilation of the SMB1 ROM to C with cycle counting + minimal PPU timing (vblank, sprite-0) | A | L | P1.1 | Differential test vs Mesen on ≥ 10M random frames incl. lag; fps recorded |
| P2.1 | Search engine v1: frame-layered BFS, state hashing, threshold objective; run on 1-1 with the objective T_set ≤ WR − 1 (H21) | A | L | P1.1 | Ties the WR in 1-1; reports whether T_set − 1 is reachable |
| P2.2 | 8-4 exhaustive search (frame-granular; Bowser RNG, L+R, ending-input trick) | A | L | P2.1 | Report: faster path (verified in two emulators) or proof record |
| P2.3 | Threshold search for framerule N−1 in each flag/pipe level, in remaining-deficit order: 4-2 top route (2), 8-3 with FPG (7), 1-2 (8), 4-1 (9), 8-1 (18), 8-2 (19) | A | L | P2.1, P0.4 | Per-level report |
| P2.4 | Cross-level DP over reachable entry states (RNG / framerule phase) | A | M | P2.2, P2.3 | Best-known full route + proof record |
| P3.1 | Static audit tool: every indexed memory access in the disassembly whose index is player-influenceable; tabulate OOB behaviors | B | M | P0.6 | `docs/oob-audit.md` |
| P3.2 | RAM oracle: single-byte perturbation sweep per level on the fast core → jackpot map | B | M | P1.1 | `docs/experiments/P3.2-ram-oracle.md` |
| P3.3 | Write-reachability: for each jackpot cell, can any in-game write hit it? | B | L | P3.1, P3.2 | Ledger entries with proof artifacts |
| P3.4 | Fuzzing / Go-Explore novelty search for anomalous states | B | L | P1.2 | Anomalies triaged in the ledger |
| P3.5 | NES Minus World re-examination with oracle + audit (WorldNumber = 36 OOB reads) | B | M | P3.1, P3.2 | Ledger entry with proof artifact |
| P4.1 | Assemble, verify in two emulators, draft submission text | ship | M | a result | User-reviewed before anything is submitted |

## Done
- 2026-08-21 — Research of the current record and community state; plan, process, and status scaffolding written (PLAN.md, PROCESS.md, this file, docs/*). Git initialized, initial commit. See docs/log.md.
- 2026-08-21 — **P0.2 done**: WR movie fetched to `data/wr/`, 17,868 frames confirmed, ROM verified against TASVideos hashes and the movie's romChecksum; `tools/fm2_info.py`, `tools/verify_rom.py`. Facts F1/F15–F17.
- 2026-08-21 — **P0.9 done**: `docs/community-claims.md` — 1-1 known as "1 frame short" since 2009 with no proof; 4-2 top route is 2 frames short (HappyLee); 8-3 FPG/242 = 3 frames; Maru's 8-4 idea; facts F35–F37, H25/H26. Still to mine: thread pp. 1–56/58/61, Maru's movie.
- 2026-08-21 — **P0.5 done**: `docs/timing-model.md` — every WR frame count derived from the code (NMI/timers/boot/loads/flag sequence/pipes/axe); T_set = grab + T + 159; control = load + 154 + w; Start rows 34–43 equivalent; facts F31–F34.
- 2026-08-21 — **P0.4 done**: framerule mechanism verified frame-exactly; slack/deficit per level (1-1 is 1 frame from the next framerule; 1-2 8, 4-1 9, 8-3 10, 4-2 13, 8-1 18, 8-2 19; 8-4 unquantized); `tools/slack_table.py`; facts F27–F30; H21–H24; `docs/experiments/P0.4-slack-table.md`.
- 2026-08-21 — **P0.3 done**: WR syncs in FCEUX and BizHawk/NesHawk with identical per-frame state; axe on fm2 frame 17867 (0-based); 24 lag frames; level-entry frames; `tools/fm2_to_bk2.py`, `tools/check_sync.py`, `tools/compare_dumps.py`, `tools/lua/wr_dump_*.lua`; dumps in `data/wr/`; facts F23–F26; `docs/experiments/P0.3-wr-sync.md`.
- 2026-08-21 — **P0.1 done**: FCEUX 2.6.6 (Lua), Mesen 2.1.1, BizHawk 2.11.1 (NesHawk) all run headless + scripted on the Linux box (toolbox container `smb1` for FCEUX/mono; no host sudo needed); wrappers `tools/*_run.sh`, reproduce with `tools/toolbox_setup.sh`; specs/versions/throughput in facts F18–F22; `docs/experiments/P0.1-tooling.md`.

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
| Ending-input coast length in WR | 19 frames: last A press on frame 17848, axe on 17867 | `tools/fm2_info.py`, `tools/check_sync.py` (V) |

## Spend
Cloud total: $0 / $300 cap.
