# Search runbook — standing rules for running the exhaustive searches

Operational rules the search campaign has earned, moved out of `STATUS.md` on 2026-08-24 so
that STATUS can stay a status. Each rule names the incident that taught it (the story is in
`docs/log.md`; the numbers are in `docs/facts.md` and `docs/experiments/`). PROCESS.md is the
work loop; this file is what to do when you actually launch a search.

## 1. Every search runs under a memory cap — no exceptions, not even a 20-second control

- **Linux box:** `systemd-run --user --scope -p MemoryMax=NG -p MemorySwapMax=0 --quiet
  /abs/path/smb-opt …` (absolute paths). An uncapped in-memory `bfsc … --check-path 47` was
  OOM-killed on 2026-08-22 20:09 and took the Claude session down with it.
- **Mac:** everything runs inside the container via `tools/mac_run.sh -m 8g -- …` (it supplies
  the cap; macOS has no `systemd-run`). See `docs/experiments/P0.11-two-box.md`.
- **Frontier and disk limits:** run `tools/watchdog.sh` alongside every dedicated run (record
  cap + free-disk floor). Verify it is alive when you check on a run — it has died silently on
  the Mac (P0.11 §7 #6). On the Mac the watchdog must `docker kill` the container, not just
  the client (P0.11 §7 #11).
- The 15 GB laptop runs **one** heavy capped job at a time (run 4 + a capped test = OOM kills
  in the journal, 2026-08-22). Layer files are ~5–25 GB each for the big runs: watch `df`.
- Bigger than the two boxes → the cloud, per PROCESS (cap $300; `docs/experiments/P0.10-cloud-sizing.md`).

## 2. Ladders and dedicated runs

- **Probe first** (~5 s): `bfscx … --goal-x GX --goal-y GY` with a small deadline prints the
  root bound ("heuristic at root"). The ladder starts there.
- **Ladder:** `MEMCAP=4G tools/bfscx_ladder.sh <prefix> <d_from> <step> <d_to> 20000000
  <layer-dir> -- <case> <chain.bin> <first> <len> --enemies 0 --threads 8`. A rung ends in
  one of three ways: **GOAL** (the segment's optimum, if the rung is the first feasible one
  and the previous rung was proof-grade dry), **no path** (frontier exhausted — a verdict),
  or **cap-killed** (a null result).
- **`max_steps` is layers from the POST-prefix root, not absolute frames** (F125, session 15). A rung
  written as `bfscx CASE INPUTS FIRST PREFIX DEADLINE` gives the search `DEADLINE` layers starting at
  the state reached after `PREFIX` steps. Passing the WR's absolute frame count as the deadline on a
  prefixed rung silently hands it `DEADLINE − h(root)` frames of slack: a prefix-162 rung given 195
  had **162** frames of slack and hit 100M states / 27 GB by layer 23. Set the deadline from the root
  bound the probe prints, not from the WR's frame numbering. (The 4-2 control gate `6584 575 587`
  looks like a counterexample but is not — it stops at layer 10 because it finds goals.)
- **Read the `--check-path` startup audit before paying for the search** (F124). `--check-path N`
  replays the reference path and prints its goal test and `N bound violations over M steps` *before*
  layer 1. That is usually the positive control you actually wanted; the exhaustive part behind it can
  cost terabytes (the 1-1 d368 rung projected ≈1.6 TB to re-derive what the audit gave in 4.7 s).
- **A cap/watchdog kill is never a "no"** (F121: the drift rungs were killed at 126M/249M
  records pinned at a wall the bound could not see). Only goal-or-exhaustion advances a
  decision tree.
- **When a rung blows the 20M ladder cap while still growing healthily** (dead ≈ 0, wavefront
  advancing), rerun it dedicated: 120–200M record watchdog, a 40–80 G disk floor, all threads
  — the "d149 treatment" (S1, S4a-i). If the frontier is growing ~×1.2/layer with 50+
  y-dormant layers to go, it will not fit: shrink the segment instead (S4a: 122.9M at layer
  41 and growing → multi-TB).
- **Frontier law:** at 2 frames of slack an open-terrain segment plateaus at ~10⁷ records/layer
  (F98); each frame of slack multiplies it. Cross-box "insurance rungs" at slack 2 are
  therefore full dedicated runs, not cheap hedges (P0.11 §7 #7). The ladder is sequential.
- **The x-only bound cannot carry a >~150-frame open-terrain segment** (F95); the y-coupled
  `ygate` bound bites only within ~25 frames of the goal — that reach is the segmentation
  ruler (cut segments so the goal is ≤ ~60–100 frames from the root; S4a-i = 60 worked,
  S4a = 112 did not).
- Cite build provenance for any Mac number (`third_party/smb-opt/.built-from`), and re-run the
  control gate after every resync (PROCESS §"Parallel work on the second host").

## 3. Seam protocol for chained segments (every seam failure so far was vertical)

1. **Gate on standable ground, before the next maneuver's commitment.** First-arrival gates
   `x ≥ GX ∧ Y ≤ GY` cannot separate an overhead arc from later ground states, cannot fence
   off above-ceiling states (the sky arc: `Y ≤ 176` admitted a y_pos page-0 state), and must
   not cut a maneuver's *staging* (the G4a/G4b split put its gate in front of the wall where
   the scroll offset is minted). Cut at the WR's own standable surfaces (floor strip, pipe-A
   cap, pipe-B top) — four consecutive seams worked that way without a re-gate.
2. **Never trust the auto-pick.** `bfscx` picks the goal parent best-by-(x speed, x); that
   pick has been a fated mid-jump, an above-ceiling arc, a ledge-forced landing. **Census the
   last layer** with `tools/pick_parent.py` (full 96-byte records; if the goal print is
   truncated recover the record by its 22-byte prefix from `layer_NNN.bin`) and pick by the
   PHYSICS fields — v_force (mind the index-encoder alias, F119), RunningTimer, the
   goal-transition input (A|R vs B|R) — not by position alone.
3. **Reconstruct TWO candidates differing in vertical situation** (grounded on the highest
   surface vs airborne-fast), chain both (`bfscx-path --enemies 0 --out …` →
   `tools/chain_inputs.py`), **probe the next segment's bound from both** (~5 s each), keep
   the healthier. Check the picked arrival against the block map before chaining.
4. **Core-verify every chain** before building on it: `tools/replay_check.py --case W42Main
   --first 6584 --prefix 0 --path <seg.bin> --enemies 0 [--down]` — 0 mismatches, or the seam
   is wrong.
5. **Keep a segment's final 1–2 layer files until the NEXT segment has chained and its early
   rungs look healthy** — not merely until the core replay passes. Deleting S4a-i's 113 G
   early cost a 66-minute rerun when a repick was needed.
6. **Probes over hand physics.** Twice a hand-derived "passes under at Y ≈ 65" / "misses the
   cap by 7 px" was wrong and a 5-second probe was right.

## 4. On a GOAL that could be a record — the pipeline (bank first, sweep second)

A verified route ≤ the framerule line is a record regardless of optimality: run it through
the pipeline immediately; the sweep queue (repicks, seam merges, proof runs) upgrades it
afterwards without blocking it.

1. Census the goal-parent layer (§3.2) → `bfscx-path` → chain (`tools/chain_inputs.py`) →
   `tools/replay_check.py … --enemies 0 --down` (expect the pipe entry: GES 3 on the last
   record).
2. Build the movie: `tools/splice_fm2.py data/wr/<WR>.fm2 <seg.bin> 6584 <out>.fm2
   --or-last 0x20 --pad 400` (WR prefix + our segment with Down OR'd into the entry record).
3. **FCEUX:** `tools/fceux_run.sh OUT=… MAXF=7600 --playmov <out>.fm2 --loadlua
   tools/lua/wr_dump_fceux.lua <ROM>`. The main area must match the model row for row —
   **and the critical check is the WARP DESTINATION** (the 553 movie failed exactly here):
   at the entry row the dump must show AreaPointer `$2F`, EntrancePage 0, parser cursor
   ≤ 15, and ~75 rows later Mario must re-enter at x 24 on ScreenLeft page 0 (the WR's
   stair-climb start) — **not** x 2072 / page 8 (the unparsed-command condition, F40/F120).
4. **BizHawk** (`tools/fm2_to_bk2.py`, `tools/bizhawk_run.sh`; it hung at 900 s once — retry,
   maybe a lower MAXF). Two emulators agreeing is the evidence standard (PROCESS).
5. Framerule math: 4-2's rule is set at the 8-1 load (F28/F29); main-area total vs the 575
   one-framerule line (588 − 13) and the 554 double line; the warp zone (WR 476, bound 461)
   is inside the same rule.
6. Document (facts, hypotheses, experiment file, log) → STATUS → commit → push. Then the
   sweep list.

## 5. Engine patch discipline

- One machine edits the engine (the primary box). The patch is `git diff` of the untracked
  clone against pin `daa4428`; regenerate it at commit time and **intent-add every untracked
  source file first** (`git add -N src/case/w42.rs src/heuristics/ygate.rs src/w42enemies.rs
  src/heuristics/drift.rs`) — a regen that dropped three of them applied cleanly and failed
  the Mac build (P0.11 §7 #13).
- **Verify by building**: `git apply` + `cargo build` + the control gate in a fresh pinned
  worktree, not `git apply --check` alone.
- Then the Mac: `tools/mac_sync_engine.sh` **run on the Mac**, then the control gate
  (`bfscx W42Main data/wr/wr_inputs.bin 6584 575 587 --lift 0 --check-path 12` → layers
  6, 16, 34, 70, 134, 673, 3472, 16472, 69489, 257001).
- Any behavior change to the search gets a regression control: the `--lift 0` gate must stay
  byte-identical when the new feature is off, and the WR's own path must survive
  `--check-path` with 0 violations when it is on.

## 6. Cleanup after a run

- Layers are re-derivable; the logs are the search record. Delete layer directories after
  the reconstruction and core verification — subject to §3.5 (keep the seam's last 1–2
  files). Record the deletion in the log so the next session does not look for them.
- On the Mac an `rm -rf` over ssh is blocked for the agent; list the directories with sizes
  under STATUS "Loose ends" for the user.
- `hcloud server list` every session while any cloud work is possible (P0.10 rules).

## 7. Beam discipline (P2.3c-8 / H39-H41)

1. **A beam is a per-layer first-arrival gate.** `--beam N` (lowest-h) and `--beam-offset` are
   *global single-key* orders, so any maneuver that pays before it gains dies on the layers it
   must survive. This is the same lossy operation as a segment seam, applied every frame. It cost
   the project a wrong verdict (F122 → F127/F128). **Never run a single-key beam and report the
   absence of something as evidence.**
2. **Two stages, always: the beam discovers, an exact rung promotes.** A bucketed beam yields
   candidates, never proofs — a beam that finds something proves existence; a beam that finds
   nothing proves nothing (the no-impossibility rule). Every promoted fact of the F103/F112-F114
   class rests on `deadline == root bound`; keep it that way.
3. **Choosing the bucket key (H40).** Cost is the *product* of the dimensions' cardinalities.
   - *Discovery* (mechanism unknown): generic physical axes — `off,y,spd,sub[,vf]`. This is what
     found the mint no one believed existed.
   - *Exploitation* (mechanism known): key on exactly the variables the downstream routine
     branches on. Worked example F130 — the 8-4 cheep frenzy reads `Player_X_Speed` as a 3-valued
     class and spawns *relative* to Mario, so its key is ≈ (timer phase, speed-class, slot
     occupancy) and absolute X is not a dimension.
   - Using a code-derived key during discovery just re-creates H39's blindness with a
     better-chosen blind spot.
4. **`--beam-max` bounds the product** by shrinking per-bucket width first; it prints
   `WARNING capped — N whole buckets dropped` before it ever drops a bucket. If you see that line,
   the run was partially greedy — say so when you report it.
5. **Objective check before ranking (H41).** Inside a framerule-flat region a saved frame is worth
   zero (F27/F28), so h-ordering ranks on noise. Where the slack is known, score exit-state quality
   and make time a hard constraint. **8-4 is exempt** — it is unquantized, so time *is* the
   objective there (H24).
6. **Census the layer by the quantity that matters.** `tools/pick_parent.py` decodes only
   x/y/speed/player-state; `smb-opt offset-census CASE LAYER_FILE [--top K] [--min N]` decodes the
   scroll offset. A goal parent picked on position alone has been wrong repeatedly (§3.2).
