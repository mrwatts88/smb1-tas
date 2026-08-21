# STATUS — SMB1 TAS project

Updated: 2026-08-21 (session 2 — P0.1, P0.3 done)
Phase: **P0 — Ground truth**
Record to beat: **17,868 frames** (HappyLee, TASVideos #1715M, 4:57.31) — last input on frame 17848 (0-based), then a 19-frame coast to the axe. A new movie must finish the game with an earlier last input.
ROM: verified byte-identical to TASVideos' (W) [!] (`tools/verify_rom.py`); classic-header copy in `roms/` on the Linux box (gitignored) — re-verified 2026-08-21.
Our best full movie: none yet
Host: Linux box (primary). Emulators: FCEUX/BizHawk in the rootless toolbox container `smb1`, Mesen2 native — run via `tools/{fceux,mesen2,bizhawk}_run.sh`, rebuild with `tools/toolbox_setup.sh` (see `docs/experiments/P0.1-tooling.md`). Git: private GitHub remote — commit after every unit, then push (document → STATUS → commit → push)

## Running jobs
(none)

## In progress
(none)

## Next up (ordered — the top unblocked item is the next unit of work)

| ID | Title | Track | Size | Depends on | Acceptance |
|---|---|---|---|---|---|
| P0.4 | Build the **slack table** from the existing dump `data/wr/fceux_wr.ram` + `.csv` (regenerate with the P0.3 command if missing): per-level frames, framerule phase (IntervalTimerControl $077F) at each flagpole/axe, frames-to-previous-framerule, lag frames, RNG ($07A7–$07AD) at each level entry, ending-input coast length | A | M | — | `tools/slack_table.py` prints the table; numbers land in docs/facts.md and Key numbers |
| P0.6 | Disassembly study #2 — warps & area loading: WarpZoneControl + WarpZoneNumbers, pipe index from Mario X, AreaPointer / WorldAddrOffsets / AreaAddrOffsets, EntrancePage / AltEntranceControl, Minus World arithmetic, warm boot ($07FD/$07FF), Bowser-replacement table, object jump tables. Write `docs/warp-model.md` | B | M | — | Every player-influenceable table index is listed with its out-of-bounds behavior |
| P0.7 | L+R / U+D semantics catalog from the code (all effects, not just the known decel); pause/Select effects on every timer | B | S | P0.5 | `docs/input-semantics.md` |
| P0.8 | Survey existing bots/tools (TASVideos thread, GitHub, speedrun.com resources): what exists, which state space each covered, source availability | C | S | — | `docs/prior-tools.md`; hypotheses ledger updated |
| P0.9 | Mine #1715M submission notes, Maru's RTA-rules TAS notes, and forum pp.1–63 for per-level claims and abandoned ideas | C | M | — | `docs/community-claims.md`; ledger seeded with every abandoned idea |
| P1.1 | Stage-1 fast core: headless libretro QuickNES harness (C/C++ or Rust) with savestate + RAM hash + input injection; benchmark fps/core | A | M | P1.2 | Stage-2 core: static recompilation of the SMB1 ROM to C with cycle counting + minimal PPU timing (vblank, sprite-0) | A | L | P1.1 | Differential test vs Mesen on ≥ 10M random frames incl. lag; fps recorded |
| P2.1 | Search engine v1: frame-layered BFS, state hashing, threshold objective; run on 1-1 | A | L | P1.1 | Ties the WR in 1-1 |
| P2.2 | 8-4 exhaustive search (frame-granular; Bowser RNG, L+R, ending-input trick) | A | L | P2.1 | Report: faster path (verified in two emulators) or proof record |
| P2.3 | Threshold search for framerule N−1 in each of the 7 framerule levels, in slack order | A | L | P2.1, P0.4 | Per-level report |
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
| WR first Start press | frame 41 (0-based) | `tools/fm2_info.py` (V) |
| WR Left+Right frames | 85 (U+D: 0) | `tools/fm2_info.py --list-lr` (V) |
| RTA-timing equivalent | 4:54.032 | S |
| RTA-rules (no L+R) TAS | 4:54.265 — 14 frames slower | S |
| Framerule | 21 frames | S |
| WR axe frame (OperMode→2) | fm2 frame 17867 (0-based) = last frame of the movie; timer 317 | `tools/check_sync.py data/wr/fceux_wr.csv data/wr/happylee-supermariobros,warped.fm2` (V) |
| WR level-entry frames (fm2, 0-based) | 1-1 42, 1-2 1944, 4-1 3766, 4-2 6042, 8-1 7723, 8-2 10813, 8-3 12956, 8-4 15057 | `tools/check_sync.py` (rows −1) (V) |
| Per-level slack table | TBD (P0.4) | — |
| Lag frames in WR (before the axe) | 24 (7 boot, 1 after Start, 16 area/pipe loads) | `tools/check_sync.py` (V) |
| Ending-input coast length in WR | 19 frames: last A press on frame 17848, axe on 17867 | `tools/fm2_info.py`, `tools/check_sync.py` (V) |

## Spend
Cloud total: $0 / $300 cap.
