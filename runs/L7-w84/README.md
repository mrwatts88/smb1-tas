# runs/L7-w84 — the 8-4 novelty sweep with the object-slot lens (L7)

**Started:** 2026-08-25 (session 21), Linux box (`build/explore`, QuickNES core).
**Command:** `runs/L7-w84/launch.sh` — read its header; it carries the roots, the lens description
and the read-out recipe. Write-up: `docs/experiments/L7-w84-sweep.md`. Facts: F265 (the sub-area
map / roots), F266 (the blind spot the lens closes).

| tag | sub-area | root | horizon | cells | MemoryMax | state |
|---|---|---|---|---|---|---|
| r5 | Bowser room (control 17590 → axe 17868) | 17577 | 400 | 60000 | 1200M | **RUNNING (Linux, s22)** — relaunched; the s21 run was stopped at 5,400 s / 21,600 (25 %) when the box was cleared for L3 and never reached the Mac. Partial kept as `r5_s21_partial.log` |
| r3 | room 3 (control 16355 → pipe 16550) | 16342 | 500 | **80000** | 1500M | **RUNNING (Linux, s22) at spec size** — see the sizing note below |
| r1 | room 1 (control 15224 → pipe 15748) | 15210 | 800 | **80000** | — | queued, Mac |
| r2 | room 2 (control 15918 → pipe 16185) | 15905 | 550 | **80000** | — | queued, Mac |
| r4 | water room (control 16720 → exit 17416) | 16707 | 950 | **80000** | — | queued, Mac |

### Sizing note (s22) — r1–r4 were about to run 25 % under spec

The spec (`docs/experiments/L7-w84-sweep.md` §, and this table) is **80,000 cells**: r5's 40,000 was a
deliberate compromise taken *because the box was busy*, and r1–r4 were to run at 80,000 "as soon as only one
`explore` remains". When s21 repointed r1–r4 to the Mac, **`launch_mac.sh` defaults to `CELLS=60000`** — sized
for fitting all *five* next to E9b — so they would have fired at 60,000 with nothing recording that as a
decision. STATUS carried both numbers in the same paragraph, which is how it slipped.

Corrected in s22: the Mac waiter was restarted as `WAIT=1 WAITN=0 CELLS=80000 SKIP='r3 r5'`. The Mac has
**18 GB** and E9b's pair sits at **1.75 GB each**, so three at 80,000 (~1.03 GB each) is ~6.6 GB total —
comfortably affordable; the 60,000 default was only ever a five-job constraint.

**r3 was pulled onto Linux and started immediately at 80,000**, rather than waiting ~4 h for E9b to exit,
because L3/H25 is now **parked** — so r3 is the *only remaining probe of room 3*, the 38-frame loss site. It
carries more weight than when it was queued, not less.

`r1`–`r4` are held by a detached `WAIT=1 WAITN=1 SKIP=r5 ./runs/L7-w84/launch.sh` (log:
`queued.log`) that polls every 60 s and launches them once only one `explore` process remains, i.e.
when the E7 archives exit. **If that waiter is gone** (`pgrep -af "L7-w84/launch.sh"` prints
nothing) and `r1`–`r4` have no logs, just run the launcher yourself — it is idempotent per tag and
`SKIP=` / `ONLY=` take space-separated tag lists.

## How to read the result

```
grep ANOMALY runs/L7-w84/*.log            # every (class, value) pair, once each
tools/e3_replay.py runs/L7-w84/anom_<class>_f<frame>.path
tail -n 3 runs/L7-w84/*.log               # the periodic line: anom=0x<mask>, goals, best
```

- **class 18** `*** SECOND STAR FLAG ***` — a slot holding `$31` beyond what the reference line
  holds here. Value = the count, bit 7 set means at least one is **live** (`Enemy_Flag != 0`), i.e.
  it would be dispatched by `ProcELoop`. A live hit is **857 frames** (1,329 with the win music,
  F258/F259) and would reopen H50, which F262 closed on the *write* side.
- **class 17** `*** OBJECT-SLOT ANOMALY ***` — a live slot holding an id the WR line never parks in
  any slot here. Not priced in advance; read it.
- **class 5** now covers all six slots ($16–$1b), so its hits are **not** comparable with
  `runs/E6-vram/`'s.
- **`r5` only:** `best_*.path` with `last_input < 17846` beats the WR's final input — a record on
  the ending-input coast (H1). The control reproduced 17846 exactly.

A dry run is a statement about the rollout policy from that root over that horizon, not a proof.
