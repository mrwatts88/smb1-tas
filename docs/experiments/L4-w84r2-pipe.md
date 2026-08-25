# L4 — 8-4 room 2's exit pipe: the 15 priced frames, and the first search ever aimed at them

**Unit:** L4 (`docs/open-threads.md`). Linux box, 2026-08-25 session 21. Written and control-gated
in a memory-bound session; one job launched small, the second left ready.

## 1. The site

`runs/E9a/loss_map.txt`, block `w84r2` (F245). Room 2 spends 55 of its 267 control frames off the
movement cap, and 23 of them are one run:

```
rows 16158-16180 ( 23 f)  x 2405->2429 (col 150-151)  y  64-100  spd +38->+23 min  +0
    blocking ahead: (r4,c152,0x10 BLOCK) (r4,c153,0x11 BLOCK) (r5,c152,0x14 BLOCK) (r5,c153,0x15 BLOCK)
```

Priced against the 2.5 px/frame bound that is **15 frames** — the fourth-largest geometric loss on
the route and the second-largest in 8-4, the only level where one frame *is* the record. The shape
is a deceleration from speed 38 to 23 while rising to `Y` 64 over the two-column block stack at
c152/c153, i.e. **an approach arc onto a pipe mouth**, not a clip.

The WR enters the pipe at **core frame 16182**, page 9 / `Player_X_Position` 132 (x 2436), `Y` 64,
x-speed 19, `GameEngineSubroutine` → 3 (dump rows 16185+; row = core + 3 here).

## 2. Why it is open, and why no earlier result closes it

MrWint's `W84Part2VertPipeEntry` proves **40 frames optimal from x 2373** (dump rows 16145 → 16185)
and the WR matches it exactly (F66/P2.5). That is a segment optimum with the state at x 2373 fixed
by construction — H39's seam corollary: **the approach chooses that state, and nothing has ever
varied it.** F245's 15 frames sit precisely inside the window the segment proof takes as given.

Nor has the site ever been searched with a key that could resolve it: every 8-4 search so far keyed
position at whole pixels. F245/F247 put these windows at **1–2 px**, and E9b's lesson (session 19,
1-2) is that a cell key with no subpixel dimension is below the resolution of the question. So the
key here carries `--subcell 16 --ysubcell 64` and `--xcell 2 --ycell 4 --spdcell 4 --relcell 2`.

## 3. The goal, and the argument that it is the right quantity (F267)

Doctrine (F230/F237): *a search goal must be the quantity the record is measured in and monotone
with it* — three proxy goals produced three fake records in session 18.

- **Goal:** `GameEngineSubroutine == 3` (pipe entry), `--baseline 16182`.
- **Monotone:** 8-4 is unquantized — no flagpole, no framerule, so a frame saved is a frame kept
  (F245/`tools/slack_table.py`). An area load costs a constant 122 frames from load to control and
  exactly one lag frame, at every ITC phase, in every level and both entry modes (F264/F265). So
  entering the correct pipe *k* frames earlier starts room 3 *k* frames earlier and reaches the axe
  *k* frames earlier.
- **The caveat that does the work: "the correct pipe."** 8-4's rooms carry loop-back pipes, and the
  40 s control run already produced one — `AreaPointer = 229` with a 255 px position jump at frame
  16223, x 1536, i.e. a rollout that entered a wrong pipe and was sent backwards. A wrong-pipe entry
  satisfies the goal and is worth nothing. **Every candidate must be core-replayed and
  destination-checked** (runbook §4.3) before it counts, exactly as for the 4-2 warp work.

## 4. Control gate (green)

```
systemd-run --user --scope -q -p MemoryMax=400M -- ./build/explore … --root 16050 --horizon 200 \
  --goal-ram 0x0e=3 --baseline 16182 --anomaly --cells 4000 --rollout 6,50 \
  --enemycell 0 --xcell 2 --ycell 4 --spdcell 4 --relcell 2 --subcell 16 --ysubcell 64 --secs 40
```

→ `GOAL frame=16182  (baseline 16182, +0)` — the seeded WR line reproduces its own pipe entry to
the frame from this root. 9,658 rollouts / 0 deaths / 2 goals in 40 s, so the goal is reachable by
the rollout policy and not a needle. Artifacts: `runs/L4-w84r2/ctrl/`.

## 5. What is running

`runs/L4-w84r2/launch.sh` (committed), two roots:

| tag | root | horizon | covers | state |
|---|---|---|---|---|
| `a` | 16050 | 200 | the 132-frame approach: the arc and its subpixel | **running** 2026-08-25, `--cells 40000` / `MemoryMax=700M`, 6 h |
| `w` | 15905 | 350 | the whole room from control 15918 — lets the approach *state* vary, not just the arc | **ready, not launched** (RAM) |

Only `a` was launched, and at 40,000 cells rather than 150,000, because the box was holding three
E7 archives (7.2 GB) plus L7's `r5`. Relaunch `a` at full size and start `w` when RAM frees:
`CELLS=150000 MEMMAX=2500M ./runs/L4-w84r2/launch.sh`.

**A goal under 16182 is a banked frame, and in 8-4 one frame is the record.** Replay
(`tools/e3_replay.py runs/L4-w84r2/goal_<frame>.path`), check the destination, price it, then sync
in FCEUX + BizHawk before it is called anything.
