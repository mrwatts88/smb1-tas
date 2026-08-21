# PLAN — Beat the Super Mario Bros. any% TAS record

Written 2026-08-21. Owner: Matt. Executor: Claude Code sessions driven by `PROCESS.md`.

## 1. Goal and success criteria

**Primary goal.** A TAS input movie for NES *Super Mario Bros.* that reaches the ending in
**fewer than 17,868 frames** (TASVideos timing: power-on to last input, 60.0988 fps) under
standard TASVideos movie rules:
- ROM: `Super Mario Bros. (W) [!].nes` (NTSC; believed identical to (JU) PRG0 — verify the
  hash against the movie header of #1715M in P0.2).
- Starts from power-on; no cartridge swap, no cheats/debug codes; deterministic emulator
  initial RAM; soft resets only if the rules allow and it actually saves time.
- Left+Right / Up+Down simultaneous inputs are allowed (TASVideos standard). If the result
  happens to use no L+R it also beats Maru's RTA-rules benchmark — a bonus, not a constraint.
- Must sync in BizHawk (NESHawk) and FCEUX; console verification desirable, not required.

**What counts as success (priority order).**
1. Any movie < 17,868 frames on the route above (a framerule anywhere, or ≥ 1 frame in 8-4).
2. Secondary: a category-creating discovery (new wrong warp / level skip / cart-swap-free
   ACE) that finishes the game in < 17,868 frames even if TASVideos files it as a new branch.
3. Fallback: an improvement to another SMB1 TASVideos branch (warpless 18:36.78, PAL warps
   4:55.16, walkathon, minimum presses, …) using the same engine. Not the primary target.

Valuable even without a record: machine-proven per-level optimality maps (they say exactly
where the remaining frames are, and they are publishable).

## 2. Ground truth (from sources, 2026-08-21; re-verify in P0 — see docs/facts.md)

| Fact | Value | Source |
|---|---|---|
| Record to beat | HappyLee "warps": 17,868 frames = 4:57.31, published 2011-01-06, FCEUX 2.2.3 | tasvideos.org/1715M |
| Previous record | klmz 4:57.33 — beaten by exactly 1 frame | tasvideos.org/1715M |
| RTA-timing equivalent | 4:54.032 | TASVideos / Wikipedia |
| RTA-rules (no L+R) TAS | Maru, 4:54.265 (4:57.54 TAS timing) — 14 frames slower | tasvideos.org/HomePages/Maru |
| Human WR | averge11 4:54.415 (2025-12-18); humans match the TAS framerule in every level except 8-4 | gamerant / Wikipedia |
| Failed re-optimizations | zdoroviy_antony 2019 subpixel-perfect rewrite = exactly 17,868; flamexx 2025 rewrite from 4-2 slower; cpt32 2025 slower | TASVideos forum p.59, user files |
| Framerule | Level end rounds up to a global 21-frame boundary; 8-4 ends on axe touch with no rounding | TASVideos Game Resources |
| Fireworks | Timer last digit 1/3/6 at flagpole → fireworks (cost frames); why 8-3 skips the flagpole glitch | Game Resources |
| ACE branch | OnehundredthCoin 4:52.65 — needs SMB3→SMB1 cartridge hot-swap to seed $7FD; separate "alternative" branch | tasvideos.org/8991S |
| ACE mechanism | World index ≥ 8 → Bowser-replacement table OOB read → object ID $C9 → behavior jump table → $D007 → state machine = 4 → jump into unmapped $53AE → open bus executes SRE ($0A),Y → RTI → PC at uninitialized $1181 | tasvideos.org/8991S |
| FDS only | Minus World gives "-3 ending" (2:44.61) and ACE "game end glitch" (5:29.957) on FDS; the NES Minus World is *believed* to loop forever | TASVideos publications |
| Route | 1-1 → 1-2 (warp) → 4-1 → 4-2 (warp) → 8-1 → 8-2 → 8-3 → 8-4 | — |
| Known TAS-only tricks | L+R 1-frame reversal (instant decel), wall clips (1-2, 4-2, 8-4), flagpole glitch, 8-4 turnaround-room subspeed ($705) trick | Game Resources, speedrun.com forum |
| Community state | TASVideos SMB1 thread: 63 pages, last post Nov 2025; no active effort on warps visible | forum pp.59–63 |

## 3. Where time can come from (the physics of the problem)

Because of the 21-frame framerule, a saved frame only matters if it crosses a boundary.
Exactly three buckets, plus cross-cutting effects:

1. **Framerule levels (1-1, 1-2, 4-1, 4-2, 8-1, 8-2, 8-3).** Must save exactly that level's
   *slack* (frames to the previous framerule boundary). The slack table is unknown to us and is
   deliverable P0.4. Slack 1–3 = live target; slack 15+ = needs a new trick.
2. **8-4.** Every frame counts: wall clip, turnaround room, water section, Bowser, and the
   *ending-input trick* — the movie ends at last input, so the final press should be a jump
   that coasts into the axe. Measure whether #1715M already coasts and by how much.
3. **Route-breaking glitch.** Wrong-warp into world 8, level skip, or cart-swap-free ACE.

Cross-cutting:
- **Lag frames.** Count them in the WR; each removable one is a free frame (and can flip a
  framerule).
- **Cross-level coupling.** Entry frame → RNG / framerule phase → enemy and Bowser patterns.
  A *slower* framerule earlier can buy frames later. Needs a DP across levels over the handful
  of reachable entry states, not per-level greedy.
- **End-of-level sequence.** Slide, walk, time-bonus countdown, fade, next-area timer, then
  framerule rounding. Build the exact model from the disassembly (P0.5); never rely on folklore.

## 4. Strategy — three parallel tracks

### Track A — the proof engine (exact-model exhaustive search)
No published work is a full-state, provably exhaustive search of every any% level; known bots
(DaSmileKat, Kriller37, periwinkle, Mars608) were narrow — vertical physics, Cheep spawns,
enemy mechanics. Build one covering the full state — position/subpixel/speed/subspeed, enemy
slots, RNG, timers, framerule phase, lag — and search each level against a *threshold*
("reach framerule N−1"), which prunes far harder than "minimize time". It proves optimality
instead of asserting it, and it finds physics-level tricks humans never tried.
Acceptance gate: it must *tie* the WR in every level before we trust it to beat one.

### Track B — glitch hunting by program analysis
The Minus World and the ACE chain are the same bug class: a table read indexed by a
player-influenced variable going out of bounds. Systematize it:
1. **Static audit** of the disassembly: every indexed read/write with a player-influenceable
   index and what each OOB value does. Priority variables: WorldNumber, LevelNumber,
   WarpZoneControl (the 12-byte WarpZoneNumbers table — what do pipe index 3 and indices ≥ 12
   yield?), AreaPointer / WorldAddrOffsets / AreaAddrOffsets, EntrancePage / AltEntranceControl,
   enemy-slot indices, object IDs and their jump tables, warm-boot/continue ($07FD/$07FF),
   OperMode and the state machine.
2. **RAM oracle.** For each level and each (address, value) single-byte perturbation, does the
   game reach the ending faster? Output: the "jackpot cells" (e.g., WorldNumber = 7 inside any
   castle means the axe ends the game). Then search backwards for in-game writes that can
   reach those cells.
3. **Fuzzing / novelty search** (Go-Explore style) on the fast core, flagging anomalous
   states: out-of-bounds positions, odd area pointers, odd state-machine values, reads of
   uncleared RAM.
4. **NES Minus World re-examination** with the oracle: WorldNumber = 36 makes many table reads
   OOB; the "dead loop" claim was established by hand, not by search.

### Track C — knowledge mining (read-only)
The 63-page TASVideos thread, #1715M submission notes, Maru's RTA-rules TAS notes, Bismuth /
Kosmic / Displaced Gamers / Retro Game Mechanics Explained breakdowns, the doppelganger
disassembly, existing bot source. Deliverables: complete trick list, known per-level slack
claims, and a list of abandoned ideas (re-run them at scale). No posting.

## 5. Infrastructure

- **Emulators.** FCEUX (the WR is .fm2; FCEUX 2.2.3 era — keep a 2.2.x build for sync
  checks), BizHawk/NESHawk (submission format, console-accurate), Mesen2 (accuracy oracle).
  Linux box = build/search host; Mac = authoring, replay, docs; cloud = search bursts.
- **Fast core, staged.**
  - Stage 1: headless libretro QuickNES (or Mesen) harness with savestates + RAM hashing +
    input injection, ~5k fps/core. Enough for P0 and the first search runs.
  - Stage 2: **static recompilation of the SMB1 ROM to C** with cycle counting (so lag and
    sprite-0 timing are right), target ~1M fps/core. Differential-test against Mesen over
    millions of random-input frames (including lag) before trusting it.
  - Fallback only: hand reimplementation of the physics. Bit-exactness is the whole game.
- **Search.** Frame-layered BFS over full-state hashes; dominance pruning only where provable
  (naive "further right is better" destroys the subpixel setups clips depend on); A* bound =
  remaining distance / max speed; threshold objective per level; DP across levels over
  reachable entry states. Parallel by frame layer; shard by hash.
- **Compute budget.** ~$50–300 total cloud (64–96 vCPU spot box, hours at a time).
  Hard cap in PROCESS.md.

## 6. Phases, deliverables, acceptance criteria

- **P0 — Ground truth (≈1 week).** Obtain #1715M .fm2; replay; per-frame RAM dump.
  Deliver: per-level frame counts, **slack table**, lag-frame count, RNG/framerule phase at
  each level entry, end-of-level timing model from the disassembly, warp/area-loading model,
  L+R semantics catalog, seeded hypotheses ledger, survey of existing bots.
  Acceptance: every number reproducible by a script in `tools/`.
- **P1 — Simulator (≈2 weeks).** Stage-1 harness, then Stage-2 recompiled core.
  Acceptance: replays the WR input file with identical RAM every frame; differential test vs
  Mesen passes on ≥ 10M random frames including lag.
- **P2 — Search (≈3 weeks).** Engine + per-level runs.
  Acceptance 1: ties the WR in every level. Acceptance 2: per-level report — either a faster
  path (verified in two emulators) or a search record proving none exists within the modeled
  state space and stated pruning assumptions.
- **P3 — Glitch hunt (parallel, weeks 2–8).** Track B items 1–4 on the fast core.
  Acceptance: audit table of every OOB-capable index; oracle jackpot map; fuzzing corpus of
  anomalous states, each triaged in `docs/hypotheses.md`.
- **P4 — Ship.** Assemble full movie, sync in BizHawk + FCEUX, optional console verification,
  draft submission text. Nothing is submitted without the user's review (decision D4).

## 7. Odds and outcome tiers (honest)

Pure-movement gains in the seven framerule levels have been hammered for 15 years by the best
TASers with bots; the unknown is whether any level's slack is small enough for a full-state
search to bridge — P0 answers that within a week. 8-4 is the most plausible conventional
frame. The glitch track is lowest probability per hour but the only path to a large drop, and
it is the least machine-searched part of this game.

Tiers: (1) machine-proven optimality maps → (2) ≥ 1 frame in 8-4 or a framerule anywhere →
new record → (3) new skip / wrong warp / cart-swap-free ACE → big record, probably a new branch.

## 8. Decisions (full log in docs/decisions.md)
- D1 Target = NES "warps", beat 17,868 frames, TASVideos rules, L+R allowed.
- D2 Category-creating glitch counts as success — secondary goal.
- D3 Other branches = fallback only.
- D4 No community engagement for now; nothing posted or submitted without the user.
- D5 Workflow = self-contained agentic loop; "continue working" must suffice in a fresh session.

## 9. Open questions
Tracked live in `STATUS.md` → "Needs user input" (ROM, Linux box access, cloud provider, git).
