# N6 — 8-3: is a glitch grab possible inside the timer-244 window? (2026-11-12, Mac)

Prompted by the user's read of the route viewer: Maru's 8-3 has many stretches below top speed.

## What the movies do (both replayed on the Mac QuickNES core, frames = core frames)

| | WR (#1715M) | Maru (RTA rules) |
|---|---|---|
| control starts | 13119 | 13119 |
| pole grab | 14486, y 17, slide (routine 4), timer 244 | 14512, y 164, glitch (routine 5), timer 242 |
| 8-4 loads | 15054 | 15054 |
| slack / deficit | 11 / 10 | 13 / 8 |

Timer ticks in 8-3 (same in both, the timer counts control frames): 244 from 14463, **243 from 14487**,
242 from 14511. 243 means three fireworks (F6), so the usable grab windows are <= 14486 (244) and >= 14511 (242).

- **Maru's mid-level slowdowns are waiting, not waste.** By position he falls behind the WR by 3 frames in the
  opening ramp (no L+R), +6 at x 432-448 (bullet launchers), +6 at x 2160-2208 (after the pipe), +4 at x 3072-3104,
  +2 at x 3280: 20-21 frames behind at x 3376. He then falls into the pole's base block (contact 14506, y 165),
  lands inside it on 14509, hops (-4 class) on 14510 and grabs rising at y 164 on 14512 - the second frame of the
  242 window. Without the waiting the same ending would grab around 14492, inside the 243 window.
- **The WR grabs on the last frame of the 244 window** (14486). `T_set = grab + T + 159` for a glitch grab against
  a 173-frame slide-and-walk (F32), so a glitch grab on or before 14486 would be worth about 47 frames in 8-3:
  two framerules for the WR (deficit 10), one-plus for Maru (deficit 8).

## The search (`endlab --flag`, new options `--xline`, `--pads`, `--fullfrom`, `--fully`)

Root: WR movie, core 14345 (on the floor before the floating steps, x 3063, speed 40). Goal: any routine-5 grab
on a core <= 14486. Prune: a node must be able to have x >= X on core 14485 at 2.5 px/frame (`--xline X 14485`);
the smallest x seen on the frame before any grab was 3411.5 (loose run from 14476) / 3411.69 (stage 2).

| run | pads | result |
|---|---|---|
| control `--flag 14470 14490 --xmin 3300 --walk 14490` | all | reproduces the WR: earliest grab core 14486, y 17, castle 14659 |
| stage 1 `--pads 0x82,0x83 --flag 14345 14486 --xline 3411 14485` | B+R / A+B+R (every full-speed jump timing) | 62,625 nodes on the last frame, 118,352 grabs on 14486, heights 17..161, **0 glitch**; 5.8 M steps, 270 s |
| stage 1 to 14490 (`--xline 3411 14488`) | same | no further grab of any kind after 14486 (floor nodes stop at the block, x 3410.94) |
| stage 2 `--pads 0x82,0x83 --fullfrom 14481 --fully 160 --flag 14345 14486 --xline 3410 14485` | full-speed jump timings to 14480, then **every pad** for near-floor nodes (y >= 160 entering 14481) | 338,050 nodes, 1,520,404 grabs on 14486, lowest heights 158 and 161, **0 glitch**; 17.5 M steps, 811 s |

Logs: `runs/N6-w83-fpg/s1_cap_jumps.log`, `s1_cap_jumps_to14490.log`, `s1_diag.log`, `s2_full_from14481.log`.
A full-pad search from 14345 (or from 14478 with y >= 150) does not fit: x3 per frame, 2.3 M nodes five frames in.

## Why it misses (from the `--diag` lines, consistent with F314's 1-1 geometry)

The full-speed (-5 class) hop off the floor goes y 176 -> 171.0 -> 166.156 -> 161.875 (A released) or 161.47.
- Grab on hop frame 3: the frame before is y 166 (side point above the block, free), the grab is at **y 161** -
  0.125 px above the glitch line (y >= 162). This is the 178,276-grab bucket.
- Grab on hop frame 2 (y 166, would be a glitch): the frame before is y 171, where the side point is in the base
  block's row, so Mario must still be left of the block column (x < 3411) and then needs x >= about 3414.2 one
  frame later: 0.7 px more than the 2.5 px cap. Same shortfall F314 found by hand in 1-1 (0.5 px).
- Falling entries land on the block (y 160, slide) or are pushed out (`ImpedePlayerMove`, no side check).
The -4 class hop (172.0 / 168.117 / 164.35) has y 168 on the frame before its y-164 frame: blocked by 0.117 px.

## Status

Not a proof. Not covered: slowdowns before core 14481 (they change only the x phase: total x room is about
1.25 px), nodes above y 160 on 14481 with non-full-speed inputs, enemy help (none is on screen at the pole),
and the clip ending (needs about 6 frames at the block, so it cannot fit before 14487).
What would overturn it: an over-cap frame at the pole (H47), a different hop phase (another take-off height
near the floor, or a y sub-pixel that survives take-off), or 25 frames found upstream (the level is at cap, F225).
