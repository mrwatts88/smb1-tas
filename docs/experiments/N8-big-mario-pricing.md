# N8 — does big Mario pay? Priced against the loss map (2026-11-13, Mac)

Asked for by the user after L8: the sweeps collected mushrooms and I had called that "ordinary" without a price.
**Verdict: not viable through brick-breaking, by arithmetic on measured numbers. Not refuted in general:** a
big-Mario-only way through a *solid* wall was not examined (none is known).

## 1. The price of being big (measured)

Replayed the two sweep paths that collected a mushroom (`runs/L8-e6-objectlens/anom_9_f6882.path` 4-2,
`anom_9_f511.path` 1-1) on the Mac core with B+Right appended:

| | power-up appears | touched | `GES` 9 (grow) | control back | freeze |
|---|---|---|---|---|---|
| 4-2 | core 6776 | 6874 | 6874-6932 | 6933 | **59 frames** |
| 1-1 | core 381 | 503 | 503-561 | 562 | **59 frames** |

- **The freeze is 59 frames and the framerule clock is stopped for all of it**: `IntervalTimerControl` ($077F)
  holds 5 (4-2) / 6 (1-1) from the touch to the release, because `TimerControl` gates the timer loop. So the 59
  frames are added to the level exactly; they are not rounded to framerules, and no slack absorbs them.
- On top of that comes the wait for the mushroom. It rises 1 px every 4 frames out of the block and then moves
  right at 1 px/frame, against Mario's 2.5. The two random paths waited 98 and 122 frames; the minimum was not
  searched. This part is ordinary movement loss and is rounded to framerules.

## 2. The WR already releases mushrooms; it never waits for one

Items the WR's own line knocks out of blocks (slot 5 going live in the WR dump): 1-2 mushroom at x 160 (core
2562) and x 2400 (3454), 1-up at x 1424; 4-1 1-up x 1472, mushroom x 2368 (4928); 4-2 mushroom x 448 (6776, at
the mint), vine x 1024; 8-1 star x 2976; 8-2 mushroom x 1600 (11617); 8-3 mushroom x 1856 (13865). So a mushroom
is available with no detour in 1-2, 4-1, 4-2, 8-2 and 8-3; the cost is the wait plus the 59.

## 3. What the losses are made of (`tools/brick_sites.py`)

The seven geometric-loss sites of F245 (290 frames), with the head-hit class of every cell around them
(solid if metatile >= `SolidMTileUpperExt` of its group, smbdis 12355; item blocks never break; the rest
shatter for big Mario, 7219-7287):

| site | loss | what blocks Mario | breakable? |
|---|---|---|---|
| 8-2 cols 201-212 | 114 | stair blocks and wall, all `$61` | no |
| 8-4 room 3 cols 214-216 | 38 | pipe `$10-$15`, castle block `$62` | no |
| 4-2 cols 23-33 | 33 | nothing: the WR waits here on purpose (the scroll mint, F93); the bricks around are `$52` | bricks yes, but the loss is not an obstacle |
| 1-2 cols 163-171 | 33 | the vertical pipe cols 168-169 (`$14/$15`), rows 0-5; the wall behind it (cols 170-176) is `$52` brick and the WR already walks through it at full speed once inside | the blocker no; the wall behind yes |
| 4-2 warp room cols 57-59 | 30 | pipes, `$61` | no |
| 1-2 cols 182-184 | 27 | nothing: the overshoot that arms the warp zone (F236) | not an obstacle |
| 8-4 room 2 cols 150-152 | 15 | pipe, castle block | no |

**197 of the 290 frames sit behind solid blocks or pipes. Of the other 93, 60 are deliberate scroll set-up (4-2
mint, 1-2 overshoot) and 33 are a pipe.** No loss site is a brick obstacle.

## 4. Arithmetic

- Per level, the geometric loss available (F245) against the price (59 exact, plus a wait of at least a framerule
  or two): 1-2 60, 4-2 63, 8-2 114, 8-4 53, the rest 0. Only 8-2 exceeds 59 + wait, and its 114 are solid.
- Even granting a free pass through the 8-2 wall: movement gain 114 minus a ~40-frame wait is 74, which is three
  framerules (deficit 19, then 21 each) = 63 frames, minus the 59 = **+4 frames**, which 8-3's framerule eats
  (deficit 10).
- The 8-3 glitch grab (H57, 42 frames) cannot be bought with size either: 42 - 59 < 0 before any wait.

## 5. Not covered

- Any big-Mario-only clip through a solid face (taller body, crouch). No mechanism is known; F327's entry rule
  (left probe inside a non-empty tile) does not depend on size, and the 8-2 wall's left neighbour column is empty.
- The minimum wait for a mushroom (state at which it becomes touchable, and where Mario can stand). Not measured.
- Fire flower, star: not priced. A star has no grow freeze (it is not `GES` 9) but changes nothing about speed.
