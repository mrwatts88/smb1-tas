# runs/L4-w84r2 — 8-4 room 2's exit pipe (L4)

**Started:** 2026-08-25 (session 21), Linux box, `build/explore` + QuickNES core.
**Command:** `runs/L4-w84r2/launch.sh` — its header carries the site, the goal argument and the
wrong-pipe caveat. Write-up: `docs/experiments/L4-w84r2-pipe.md`. Fact: F267.

| tag | root | horizon | covers | state |
|---|---|---|---|---|
| `a` | 16050 | 200 | the 132-frame approach — the arc and its subpixel | running, `--cells 40000` / `MemoryMax=700M`, 6 h |
| `w` | 15905 | 350 | the whole room from control 15918 — the approach *state*, not just the arc | not launched (RAM) |

`ctrl/` holds the 40 s control gate: `GOAL frame=16182 (baseline 16182, +0)`.

## How to read the result

```
grep GOAL runs/L4-w84r2/a.log          # "GOAL frame=N (baseline 16182, ±k)"
tail -n 3 runs/L4-w84r2/a.log          # goals / best / maxx
tools/e3_replay.py runs/L4-w84r2/goal_<N>.path
```

- **baseline 16182 = the WR's own pipe entry.** Anything **below** it is a banked frame, and 8-4 is
  unquantized, so one frame is the record (F245/F267).
- **Before believing any of it: check the destination.** Room 2 has loop-back pipes; the control run
  produced one (`AreaPointer = 229`, a 255 px position jump). A wrong-pipe entry satisfies the goal
  and is worth nothing. Runbook §4.3, then FCEUX + BizHawk (PROCESS).
- When RAM frees: `CELLS=150000 MEMMAX=2500M ./runs/L4-w84r2/launch.sh` runs both roots at full size.
