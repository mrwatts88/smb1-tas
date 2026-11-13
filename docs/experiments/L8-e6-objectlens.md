# L8 — E6's six roots re-run with the object-slot lens

**Date:** launched 2026-11-12 19:57 CST on the Fedora box, finished 2026-11-13 01:57 CST, read out 2026-11-13.
**Verdict:** dry. Class 18 (a second `StarFlagObject`, priced at 857 frames, F258) fired on **no** root.
Class 17 (a novel `Enemy_ID` in a live slot) fired three times; all three were replayed on the core and are
ordinary. **This is a statement about the rollout policy from these roots over these horizons, not a proof.**
The horizons leave gaps (§4); L8b is running on them.

## 1. Setup

`runs/L8-e6-objectlens/launch.sh` (a copy of `runs/E6-vram/launch.sh` with the output directory changed), box
clone at 3d6a6a4, `build/explore` rebuilt there. Six processes, 1.5 GB and 21,600 s each:

```
./build/explore CORE ROM data/wr/wr_inputs.bin --root R --horizon H --max-addr 0x300 --max-weight 20 --prog-fw 1
  --anomaly --cells 80000 --rollout 6,50 --enemycell 0 --xcell 8 --ycell 16 --spdcell 16 --relcell 32
  --seed S --secs 21600 --report 300 --out runs/L8-e6-objectlens
```

Why it is not a repeat of E6: F266. E6's nearest class saw only ids above `$36` in five of six slots, so `$31`
was invisible. This binary has class 17, class 18, and class 5 over all six slots.

## 2. Per root

| root | level | root / horizon | rollouts | frames | deaths | max x | max VRAM offset | `anom` mask | classes that fired |
|---|---|---|---|---|---|---|---|---|---|
| w12 | 1-2 | 2483 / 1290 | 5,771,221 | 144.19 M | 224,986 | 3057 | 55 | `0x30e1b` | 0 1 3 4 9 10 11 16 **17** |
| w42 | 4-2 | 6582 / 700 | 7,654,743 | 188.34 M | 751,648 | 2091 | 45 | `0x11213` | 0 1 4 9 12 16 |
| w11 | 1-1 | 193 / 380 | 7,557,639 | 180.41 M | 202,102 | 945 | 37 | `0x20303` | 0 1 8 9 **17** |
| w41 | 4-1 | 3920 / 1450 | 8,298,853 | 189.87 M | 1,240,307 | 3475 | 49 | `0x22b43` | 0 1 6 8 9 11 13 **17** |
| w82 | 8-2 | 10970 / 2000 | 5,306,504 | 133.64 M | 876,494 | 3555 | 67 | `0x17a53` | 0 1 4 6 9 11 12 13 14 16 |
| w83 | 8-3 | 13110 / 1350 | 8,782,386 | 186.34 M | 1,561,258 | 3348 | 35 | `0x04203` | 0 1 9 14 |

Total 43.4 M rollouts, 1.02 billion frames. `goals=0` on every root (no goal was set; these are novelty sweeps).

**Never fired on any root:** 2 (`OperMode`), 5 (`Enemy_ID` out of table), 7 (`VRAM_Buffer1_Offset` > 80),
15 (`DuplicateObj_Offset`), **18 (second star flag)**. The largest VRAM offset reached is 67, the WR's own
maximum (F234); the `$06D6` redirect needs 227.

## 3. Triage

### Class 17: three hits, each replayed on the core

Replay tool: `tools/slot_replay.py PATHFILE FRAME [SPAN]` (new; stdlib only, prints all six slots with their
`Enemy_Flag`. `tools/e3_replay.py` prints five and needs numpy, which neither machine has). Paths are committed:
`runs/L8-e6-objectlens/anom_17_f*.path`.

| root | value | frame | what the replay shows | verdict |
|---|---|---|---|---|
| w12 | `$30` | 3666 | Mario took the ordinary exit pipe at the end of 1-2 and is rising out of the pipe in the outdoor exit area (GES 7, x 2872). Slot 5 holds `$30` live at x 3160, y 48: that area's own `FlagpoleFlagObject`. Novel only because the WR leaves 1-2 through the warp zone and never loads this area. | ordinary |
| w11 | `$2e` | 375 | Mario bumped 1-1's first power-up block (x 336): slot 5 holds `$2e` `PowerUpObject`, state 1 then 2 (rising out of the block). The same root later fires `GES = 9` and `PlayerSize = 0`, i.e. he collected it. | ordinary |
| w41 | `$01` | 5097 | A Spiny (`$12`) in slot 0 becomes id `$01` on frame 5096, state 2, knocked up and left. Mario (small, rising, x 2456) has just bumped the block it stood on; his speed goes −27 → 0 on the same frame. Mechanism below. | real quirk, ordinary by the census (F261) |

**The 4-1 hit is `Demote`, and the id it writes is one bit of the enemy's screen position (F330).**
`HandleEToBGCollision` (smbdis 12436) runs when an enemy stands on the bounced-block placeholder `$23`. For any
non-Goomba id below `$15` it falls into `GiveOEPoints`, whose `jsr SetupFloateyNumber` returns with
A = `Enemy_Rel_XPos` (11539), and then into `ChkToStunEnemies`, which compares A as though it were still the
enemy id (the disassembly's own comment at 12460 says so). A in {9, 13, 14, 15, 16} reaches
`Demote: and #%00000001 / sta Enemy_ID,x`. `RunNormalEnemies` calls `RelativeEnemyPosition` before
`EnemyToBGCollisionDet` for the same slot, so A is this enemy's own on-screen x. In the replay: `ScreenLeft` 2433,
Spiny x 2448, screen x **15**, and the id becomes 15 & 1 = **1**. So: bump the block under a non-Goomba ground
enemy while its on-screen x is 9 or 13–16 and it becomes id `$00` or `$01`.

This does not reopen H50. F261's census of every store into `Enemy_ID` already lists "`Demote`'s
`and #%00000001`": the value set is {0, 1}, and `$31` is not in it. No use for a Koopa on the route is known.
Not searched for one.

### The other classes

| class | values seen | reading |
|---|---|---|
| 0 `Y above world` | 250–255, all roots | Mario above the top of the screen on a high jump. The WR's line never does it at these spots. |
| 1 `GES` | 9 (grow), 2 / 3 (side / down pipe), 4 (normal flagpole slide, 8-2) | power-up collected; pipes the WR does not take; an ordinary grab where the WR uses the glitch grab |
| 8 `Player_State` 2 | 1-1, 4-1 | the falling state, which the WR's line through those two stretches never enters |
| 9 `PlayerSize` 0 | all six | big Mario, seven frames after each `GES = 9` |
| 3 / 4 / 10 / 11 on w12 | `WorldNumber` 1, 2, 4, 35; `AreaPointer` 36, 40, 42, 1, 64; `WarpZoneControl` 5; `AltEntranceControl` 1, 2 | 1-2's warp pipes to worlds 2 and 3 (the WR takes 4); the exit pipe; and the early-entry row {−1, 5, −1}: world 5 and the Minus World. F42 (Minus World is a loop) and F235 (row {8,7,6} is closed in 1-2). `WarpZoneControl = 5` appears 11 frames **after** `WorldNumber = 4`, i.e. it is the warp object re-run with the new world number, not a cause. Not replayed. |
| 4 / 12 / 16 on w42 | `AreaPointer` 66 at x 1349; `ScrollLock` 1 and a 255 jump at frames 7243–7244 | the WR's pipe (x 1348) entered without the WR's scroll set-up, so it leads to its ordinary destination; then an area entry. Read from the positions, not replayed. |
| 6 / 13 | `EnemyFrenzyBuffer` 18 (`$12`), `EnemyFrenzyQueue` 24 (`$18`), 4-1 and 8-2 | Lakitu's own Spiny frenzy; both values are in F262's writable sets |
| 12 on w82 | `ScrollLock` 2 … 59 at x 3449 | `inc ScrollLock` (12173) once per frame of an ordinary flagpole slide |
| 14 | `SecondaryHardMode` 1, 8-2 and 8-3 | an absolute predicate (`$06CC != 0`); the WR's own line holds 1 throughout world 8 (checked in the WR RAM dump). A false positive of the class definition. |
| 16 | 255 / 216 on w12, 255 on w42 and w82, 6–14 px on w82 | area changes (the position resets); 10–12 px vertical at x 703–707 in 8-2 (y 394 → 362 in three frames, the springboard there); 6 / 14 px at x 3449–3463, the flagpole snap. Not replayed. |

## 4. What these runs did not cover

The roots and horizons are E6's. Against the WR's controllable frames per room (from `tools/route_viewer.py` on
the WR movie):

| stretch | WR control frames | covered by L8? |
|---|---|---|
| 1-1 room 1 | 193–560 | yes (193–573) |
| 1-1 coin room | 652–762 | **no** |
| 1-1 after the pipe, flagpole | 1045–1284 | **no** |
| 1-2 | 2483–3762 | yes |
| 4-1 | 3978–5420 | to 5370: **stops 50 frames before the grab** (x 3475 of 3590) |
| 4-2 main room | 6581–7168 | yes |
| 4-2 warp-zone room | 7244–7719 | **no** (38 frames at most) |
| 8-1 | 7930–10340 | **no — 8-1 was never in the set** |
| 8-2 | 10976–12471 | yes, through the flagpole |
| 8-3 | 13119–14485 | to 14460: **stops 25 frames before the grab** (x 3348 of 3412) |

**L8b** (`runs/L8b-gaps/launch.sh`, launched 2026-11-13 13:36 CST on the box, same binary and flags) covers the
six uncovered stretches: `w81` 7930 / 2500 (6 h), `w11coin` 652 / 140 (1 h), `w11tail` 1045 / 400, `w42warp`
7244 / 520, `w41end` 5250 / 300, `w83end` 14330 / 300 (2 h each). Read-out goes in §5 below.

## 5. L8b read-out

(pending; the 2 h roots finish about 15:36 CST, `w81` about 19:36 CST on 2026-11-13)
