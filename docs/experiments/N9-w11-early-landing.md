# N9 — 1-1: land in the pole's base one frame earlier (2026-11-13/14, Mac)

The specified-but-never-run follow-up to H56 (F318): the castle walk in 1-1 has a one-frame lever, one frame is a
framerule there (deficit 1), and the only search (N3, root core 1262) started after Mario was already falling at
the top falling speed. Anything that needs him lower at the pole has to change the last jump, which starts on
core 1230.

**Verdict so far: not reachable by an earlier jump. Search record plus a counting argument; not a proof for
every approach.** The run's final tally (grabs on core 1285 and their castle frames) was still running when this
was written; see "Open" below.

## What the WR does (trace, core frames)

Last jump from the top stair (y 48): on the ground on 1229, rising from 1230, A held one frame, apex y 19, falling
at 4 px/frame from 1246. x is on the cap line: 3155.9375 on 1278, so the first frame inside the base-block column
(x >= 3156) is **1279**, at x 3158.4375, y 165. From there:

| core | y | x | what happens |
|---|---|---|---|
| 1279 | 165 | 3157.44 | feet 5 px into the block: pushed left 1, speed 0 |
| 1280 | 169 | 3158.38 | Left+Right: moving direction left, pushed right 1 |
| 1281 | 173 | 3159.38 | pushed right 1 |
| 1282 | 176 | 3158.50 | lands, pushed left 1 |
| 1283-1284 | 172, 168 | 3158.4 | hop (slow class) |
| 1285 | 164 | grab | glitch grab; castle on 1411, 1-2 loads on 1943 |

## The test

`--set 1229=0x83 --set 1230=0x00` moves the jump one frame earlier with nothing else changed. Mario is then 4 px
lower on every frame of the fall: y 169 on 1279, y 173 on 1280, **lands on 1281**, one frame sooner. A grab on
1284 would put the castle on 1410 and load 1-2 on 1922.

```
build/endlab CORE ROM data/wr/wr_inputs.bin --input-skip 2 --set 1229=0x83 --set 1230=0x00 \
    --flag 1262 1286 --xmin 3090 --walk 1290 --maxnodes 4000000 --out runs/N9-w11-early-land/a_jump1229.bin
```

Every input from core 1262 on (16 pads on the floor, A/L/R rising, L/R falling), dedup on the player's physical
state. Same search as N3's `walk_1262`, from the earlier-jump state. Log: `runs/N9-w11-early-land/a_jump1229.log`.

| after core | nodes | grabs (slide / glitch) | best x standing on the floor | best x rising at y 165-167 |
|---|---|---|---|---|
| 1282 | 144,034 | 0 / 0 | **3157.3125** | - |
| 1283 | 594,399 | 0 / 0 | 3157.25 | 3157.4375 |
| 1284 | 2,060,537 | 5,980 / **0** | 3157.19 | 3157.31 |

**No glitch grab on core 1284 or earlier.** A grab needs x >= 3158.0; the deepest floor state after the early
landing is 0.6875 px short.

## Why (counting)

Inside the column Mario gains exactly one pixel per falling frame after the entry frame (the right-pushes) and
loses one on the entry frame and one on the landing frame. With the entry fixed on 1279 by the speed cap:

x after landing on core L  =  3158.4375 - 1 + (L - 1280) - 1  (+ a few sixteenths)

- L = 1281 (this test): 3157.4, outside the grab zone. No grab.
- L = 1282 (the WR): 3158.4. Grab on 1285. The lever then needs x >= 3158.6875 with moving direction right, or
  moving direction 0 / 3 (F318); N3's search from 1262 covers every input for this landing frame and finds
  neither.
- L = 1283: 3159.4, deep enough for the lever, but the grab is on 1286, so the castle is 1411 again.

Each pixel of depth costs one frame of falling and the lever is worth one frame. That is the same statement as
H56's "a third right-push", now with the frame it costs.

## A tool bug found on the way (affects one label in N6, no result)

Since N6 (commit eab425c) `endlab --flag` without `--pads` used only B+Right and A+B+Right: the restriction tested
`npads > 0`, and a default added on 2026-11-09 for another mode always fills two pads. Fixed here (`padsgiven`).
Checked against N3's log: the first frames from core 1262 are 3, 8, 19, 40, 77 nodes again. **Affected:** N6's
control row, labelled "all" pads; it ran with the two full-speed pads (it still reproduced the WR's grab). N6's
stage 1 and stage 2 passed `--pads` explicitly and are unaffected; N7's runs passed `--pads` as well.

## Open

- The run's last frame (grabs on core 1285 from the early-landing state, 2 M nodes) had not finished; it can only
  show grabs on the WR's own frame or later.
- Arcs other than "same jump, one frame earlier" (a different hop pattern up the stairs, a drop from a lower
  step) were not searched. By the counting above they can change only L, and every L is covered.
- An entry frame other than 1279 needs more than 2.5 px/frame (H47).
