# STATUS — SMB1 TAS project

Updated: 2026-08-21 (session 1 — planning only; no engineering yet)
Phase: **P0 — Ground truth**
Record to beat: **17,868 frames** (HappyLee, TASVideos #1715M, 4:57.31)
Our best full movie: none yet
Git: initialized 2026-08-21 — commit after every unit (document → STATUS → commit)

## Running jobs
(none)

## In progress
(none)

## Next up (ordered — the top unblocked item is the next unit of work)

| ID | Title | Track | Size | Depends on | Acceptance |
|---|---|---|---|---|---|
| P0.1 | Tooling install on the Mac: FCEUX (scriptable/Lua), BizHawk or Mesen2; record versions | infra | S | — | Each launches headless/scripted; versions in docs/facts.md |
| P0.2 | Fetch the #1715M movie file (.fm2) from https://tasvideos.org/1715M into `data/wr/`; parse the header (ROM checksum, frame count, emulator) with `tools/fm2_info.py` | A/C | S | — | Frame count == 17,868; ROM hash recorded in docs/facts.md |
| P0.3 | Sync the WR: replay the .fm2 in FCEUX (and BizHawk via conversion) with the user-supplied ROM; confirm the 8-4 axe/ending is reached | A | S | P0.1, P0.2, ROM | Movie reaches the ending; any desync documented |
| P0.4 | Per-frame RAM dump of the WR (Lua) → `data/wr/` + CSV of key addresses; build the **slack table**: per-level frames, framerule phase at flagpole/axe, frames-to-previous-framerule, lag frames, RNG state at each level entry, ending-input coast length | A | M | P0.3 | `tools/slack_table.py` prints the table; numbers land in docs/facts.md and Key numbers |
| P0.5 | Disassembly study #1 — timing: IntervalTimerControl / framerule counter, end-of-level sequence (slide, walk, time-bonus countdown, fade, next-area timer), pipe/area transitions, lag (NMI overrun). Write `docs/timing-model.md` | C | M | — | Model predicts the WR's level-end frames exactly (checked against the P0.4 dump) |
| P0.6 | Disassembly study #2 — warps & area loading: WarpZoneControl + WarpZoneNumbers, pipe index from Mario X, AreaPointer / WorldAddrOffsets / AreaAddrOffsets, EntrancePage / AltEntranceControl, Minus World arithmetic, warm boot ($07FD/$07FF), Bowser-replacement table, object jump tables. Write `docs/warp-model.md` | B | M | — | Every player-influenceable table index is listed with its out-of-bounds behavior |
| P0.7 | L+R / U+D semantics catalog from the code (all effects, not just the known decel); pause/Select effects on every timer | B | S | P0.5 | `docs/input-semantics.md` |
| P0.8 | Survey existing bots/tools (TASVideos thread, GitHub, speedrun.com resources): what exists, which state space each covered, source availability | C | S | — | `docs/prior-tools.md`; hypotheses ledger updated |
| P0.9 | Mine #1715M submission notes, Maru's RTA-rules TAS notes, and forum pp.1–63 for per-level claims and abandoned ideas | C | M | — | `docs/community-claims.md`; ledger seeded with every abandoned idea |
| P1.1 | Stage-1 fast core: headless libretro QuickNES harness (C/C++ or Rust) with savestate + RAM hash + input injection; benchmark fps/core | A | M | P0.3 | Replays the WR with identical RAM each frame vs the FCEUX dump; fps recorded |
| P1.2 | Stage-2 core: static recompilation of the SMB1 ROM to C with cycle counting + minimal PPU timing (vblank, sprite-0) | A | L | P1.1 | Differential test vs Mesen on ≥ 10M random frames incl. lag; fps recorded |
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

## Blocked / Needs user input
- **ROM**: place `Super Mario Bros. (W) [!].nes` in `roms/`. Expected MD5
  `811b027eaf99c2def7b933c5208636de` (unverified recollection — P0.2 confirms it from the
  movie header). Blocks P0.3 and everything after it; P0.1, P0.2, P0.5–P0.9 can proceed now.
- **Linux machine**: hostname / SSH access and specs (cores, RAM). Not blocking P0.
- **Cloud**: preferred provider and how to authenticate. The Railway MCP that is available is
  not a good fit for CPU-burst search; a plain VM provider (spot/preemptible) is. Needed by P2.

## Key numbers (each must be reproducible by a script in tools/)
| Quantity | Value | Source / script |
|---|---|---|
| WR movie length | 17,868 frames (4:57.31) | TASVideos #1715M (S) |
| RTA-timing equivalent | 4:54.032 | S |
| RTA-rules (no L+R) TAS | 4:54.265 — 14 frames slower | S |
| Framerule | 21 frames | S |
| Per-level slack table | TBD (P0.4) | — |
| Lag frames in WR | TBD (P0.4) | — |
| Ending-input coast length in WR | TBD (P0.4) | — |

## Spend
Cloud total: $0 / $300 cap.
