# runs/H35-w42warp — 4-2's warp zone (H35), the one priced loss site never searched

**Started:** 2026-11-07 ~12:30 (box local time), Linux box, `build/explore` + QuickNES core. **Ends:** ~18:35 (6 h each).
**Command:** `runs/H35-w42warp/launch.sh` (header has the site, goal, thresholds and promise choice).

| tag | root (core) | horizon | promise | covers |
|---|---|---|---|---|
| `a1`, `a2` | 7602 | 170 | `--prog-x 810 --max-addr 0xce --max-weight 1` | roof at x 874, full speed -> brake, gap, drop, return to the pipe |
| `w1`, `w2` | 7246 | 520 | default (rightward) | whole warp zone from control — lets the roof-run state vary |

120,000 cells, `MemoryMax=2000M` each. Two seeds per root, as L7, so convergence can be read.
`w*_ybias_killed.log` = first `w` launch with the Y bonus, which pulled the floor start into pits; killed after ~2 min.

**Control gate (green):** `ctrl/ctrl.log` — root 7602, 40 s, 4,000 cells -> `GOAL frame=7721 (baseline 7721, +0)`.
All four full runs also printed `GOAL frame=7721 (+0)` from their seeded WR line at startup.

## How to read the result

```
grep GOAL runs/H35-w42warp/*.log           # "GOAL frame=N (baseline 7721, ±k)"
tail -n 2 runs/H35-w42warp/{a1,a2,w1,w2}.log
```

- Goal = `GameEngineSubroutine == 3` **and** `WorldNumber == 7` (pipe entry, world-8 pipe). WR = core **7721**.
- **< 7721** banked. **<= 7711** framerule together with F88's 3 main-area frames (needs a splice check on
  the core). **<= 7708** framerule on its own. Then FCEUX + BizHawk per PROCESS.
- Path files: `runs/H35-w42warp/<tag>/goal_<N>.path` (replay = WR inputs to the root, then the path).
