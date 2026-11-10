# N3 — Castle-walk skip at the flagpole without an enemy (H54)

2026-11-09 to 2026-11-10, Mac (QuickNES core 26bb785, `build/endlab`). The Fedora job (H52) was not touched.

## Question

The 8-2 ending (Bullet Bill bounce) enters the castle one frame after the flagpole grab. The
flagpole glitch used in 1-1, 4-1 and 8-1 waits 24 frames on the pole, hops off and walks to the
castle door: 126 frames. Can the 8-2 style ending be had without an enemy? The prize is 6
framerules per level, and 1-1 needs only 1 frame (F29), so up to about 100 frames of setup would
still pay.

## What was measured (F314)

`endlab --pokescan T ADDR LO HI STEP` pokes one RAM byte after core frame T and reports the frame
`StarFlagTaskControl` (`$0746`) first becomes non-zero (castle entry) and the next area load. The
unmodified movie is the control in every run.

| poke on the WR's 1-1 | castle entry | 1-2 loads |
|---|---|---|
| none (control) | 1411 | 1943 |
| `Player_Y_Position` 165–172 on the grab frame (core 1285, movie 164) | 1287 | **1817** |
| `Player_Y_Position` 160–164 | 1411 | 1943 |
| `Player_XSpeedAbsolute` (`$0700`) ≥ 25 on the landing frame (core 1282, movie 2) | 1286 | **1817** |
| `$0700` = 23, 24 | 1411 | 1943 |

So the prize is real (126 frames), and with the WR's own inputs it hangs on one byte: `$0700` ≥ 25
at the hop makes the hop fast-class (−5: Y 171, 166) and the grab happens at Y 166 instead of 164.

Commands (`E` = `build/endlab third_party/QuickNES_Core/quicknes_libretro.dylib roms/smb.nes data/wr/wr_inputs.bin --input-skip 2`):

    E --pokescan 1285 0xce 158 172 1
    E --pokescan 1282 0x700 23 26 1
    E --pokescan 1285 0x400 0 255 1
    E --pokescan 12470 0xce -1 -1 1      # 8-2 control: castle 12473, load 12955
    E --trace 1252 1288

## Why it cannot be reached at a flat pole (code-level argument)

Setting: small Mario, flat floor (standing Y = 176) left of the pole, no enemy, spring, vine or
platform. Pole column at pixels P…P+15 (1-1: P = 3168): rows 0–9 are climbable (ball, shaft), row
10 (pixels 192–207) is the solid base block. Small Mario's collision points (`BlockBuffer_X_Adder`
/ `_Y_Adder`, offset `$0e`): feet (X+3, Y+32) and (X+12, Y+32); sides (X+2, Y+24) and (X+13, Y+24).
x moves on a 1/16 px grid (`MoveObjectHorizontally` adds speed × 16 to the sub-pixel byte).

1. **The skip needs Mario on the pole at Y ≥ 165.** `PlayerEndLevel` (5831) starts the castle
   tasks when `Player_CollisionBits` d0 is clear. Only `ImpedePlayerMove` (12318) with a "right"
   argument clears it: the foot check with a foot 5 or more px inside a solid tile and
   `Player_MovingDir` = 1 (`ChkFootMTile` 11997), or the side check with the right point in a solid
   tile. On the pole (X snapped to P−7) both need Y ≥ 165 (foot) or Y ≥ 168 (side).
2. **On the pole Y only changes by the automatic slide** (routine 4, stops at 158/159) **and by
   `LandPlyr`** (snaps 160–164 to 160). So the grab itself must be at Y ≥ 165.
3. **A grab is made only by the side check** (`HandleClimbing` 12153): side point in a climbable
   tile (Y ≤ 167) and X & 15 in 6–9 (X in P−10…P−7). So Y is 165, 166 or 167.
4. **The grab must be rising.** At those heights the right foot is 5–7 px inside the base block;
   when `Player_Y_Speed` ≥ 0 the foot check jumps to `ImpedePlayerMove` and returns without a side
   check.
5. **Rising needs `InitJS`.** Every writer of `Player_Y_Speed` was read (smbdis 6058 climbing, 6123
   jump, 6660 jumpspring, 7314 bump = 0, 7386 brick shatter, 11432 death, 11478/11512 stomp, 11791,
   11861, 11973, 12021 landings). Without an enemy, spring or brick only the jump is left.
6. **Only the fast-class hop passes through 165–167.** From Y 176 the first frames are 172, 168,
   164 (classes 0–2, any A pattern) or 171, 166, 161 (classes 3–4). The class is read from
   `Player_XSpeedAbsolute` (`$0700`) ≥ `$19` at `InitJS`. So: fast hop on frame J, grab on J+1 at
   Y 166 with X(J+1) in P−10…P−7.
7. **Kinematics of the hop.** On frame J (Y 171) the side point is in the block row, so the right
   point collides when X ≥ P−13; with speed ≥ 0 Mario is pushed 1 px left and stopped.
   - No contact on J: X(J) ≤ P−13−1/16, so X(J+1) ≤ P−10.5625. **Short by 9/16 px** (needs 3.0625
     px in one frame; the cap is 2.5).
   - Contact on J, or speed < 0 on J: Mario must already stand on the floor at X ≥ P−10.1 at the
     end of frame J−1 with `$0700` ≥ 25.
8. **No such floor state exists.** `$0700` is rewritten to the true speed by `ImposeFriction` on
   every floor frame and on every airborne frame with Left or Right held.
   - Floor frame with real speed ≥ +25: the frame before, the right point was already inside the
     block with speed ≥ 0, so he had been pushed and stopped. Contradiction.
   - Landing frame with the byte stale from a rightward flight: `Player_MovingDir` stays 1, so every
     contact frame (foot or side) pushes left. The first contact leaves him at most at P−11.5625.
   - The WR gets to P−10 only by pressing Left+Right in the air after the first push: the speed goes
     to −1, `Player_MovingDir` becomes 2, and the next two foot-deep frames push him right. That
     press runs `ImposeFriction` and sets `$0700` to 1.
   - Leftward speed ≥ 25 would need Mario to start right of P−8, i.e. to have crossed the 4 px grab
     zone on frames without a side check. Only foot-deep falling frames skip it, he moves 1 px per
     such frame, and a fall through Y 165–175 has at most three of them.

The same argument applies to 4-1 and 8-1 (flat floor before the pole, flag glitch in the WR) and
to 8-3's pole (112 px of flat floor after the pit, `python3 tools/area_data.py L_GroundArea2`).
It does not apply to 8-2, where the Bullet Bill supplies the rising speed.

## Search record

`endlab --flag F0 F1 [--xmin X] [--walk N]`: breadth-first over every input (all A/B/L/R pads on
the floor; A/L/R while rising, L/R while falling, where B is not read and L+R acts as one of
them), dedup per frame on the player's physical state (`flag_key`), goal `$0746` non-zero within 6
frames of a grab. Every grab is counted by routine (4 slide, 5 glitch) and height.

**Positive control** (8-2, ten frames before the WR's bounce):

    E --flag 12462 12476 --xmin 3300 --show 1

finds the skip on its own: 736 paths, all at y 165 on core 12472; 8,244 glitch grabs at y 164
without the skip; slides at y 150–160. 436,333 steps, 19 s.

**1-1 from core 1262** (23 frames before the WR's grab, Mario falling at x 3116, speed 40):

    E --flag 1262 1300 --xmin 3090 --maxnodes 2000000 --show 3   # log: runs/N3-flag/f1262.log

| after frame | nodes | glitch grabs | slides | skips | floor max x | floor max x with `$0700` ≥ 25 | max x rising at y 165–167 |
|---|---|---|---|---|---|---|---|
| 1282 | 13,253 | 0 | 0 | 0 | 3158.500 | 3156.125 | — |
| 1283 | 56,206 | 0 | 0 | 0 | 3158.438 | 3155.938 | — |
| 1284 | 195,890 | 0 | 0 | 0 | 3158.375 | 3155.562 | **3156.438** |
| 1285 | 625,210 | 1,588 | 0 | 0 | 3158.250 | none | 3155.938 |
| 1286 | 1,747,921 | 3,668 | 624 | 0 | 3158.125 | none | 3155.562 |

Stopped by hand during the next layer (7.6 M steps, 348 s; the frontier grows about 3× per frame
once Mario stands, and the next layer would not fit in 18 GB). **No skip in 4,292 grabs.** The
first glitch grab is on core 1285, the WR's own frame. The best rising x at y 165–167 is 3156.4375
= P − 11.5625, exactly the bound of step 8; a grab needs 3158.0. The floor maximum with `$0700` ≥ 25
is 3156.125; step 7 needs 3157.9.

Coverage: every input from core 1262 through 1286, which is every air-control choice on the WR's
approach, every landing, the one frame on which the byte is still stale, and four more frames. It
does not cover run-ups longer than that; those are covered by the argument (any later approach is
again a rightward flight or run into the block and meets step 8).

## Conclusion

H54 is refuted for an enemy-free flat pole (1-1, 4-1, 8-1, 8-3) by the code-level argument above,
with the bounded search agreeing to the sub-pixel. Extra setup frames do not help: the blocker is
geometric (a 2.5 px per frame cap against a 3.0625 px gap, and a right-push that costs the stale
byte), not a matter of time.

## Walk timing: can any grab variant save the one frame 1-1 needs?

    E --flag 1262 1286 --xmin 3090 --maxnodes 2000000 --walk 1286   # log: runs/N3-flag/walk_1262.log

`--walk N` follows the automatic slide, wait, hop and walk for every grab up to core N and tallies
the castle-entry frame. 4,292 grabs (3,668 glitch grabs at y 164; 624 slides at y 156–161):

| castle entry (core) | 1411 | 1412 | 1413 | 1414 | 1445 | 1446 | 1451 |
|---|---|---|---|---|---|---|---|
| grabs | 632 | 1,004 | 128 | 1,904 | 96 | 96 | 432 |

The earliest is 1411, the WR's own frame; 1410 would have loaded 1-2 one framerule earlier (F314).
8,163,629 steps, 383 s.

## 8-2: can the Bullet Bill come earlier?

Mario can be at the 8-2 pole 112 frames before the WR (F247), so an earlier bounce there would
pay. It cannot come earlier:

- `BulletBillHandler` (smbdis 6824): a new bullet flies toward the player at `$18` (1.5 px per
  frame) and is erased if the player is within 40 px of the cannon on either side, or if it is fully
  off screen. A bullet that flies right toward the pole needs Mario at least 40 px right of the cannon.
- The cannon is the floor-level one at page 11 column 15 (x 3056, bullet y 184). In the WR it fires
  on core 12220–12221 with Mario at x 3098–3101, the first or second frame he is 40 px past it
  (`E --trace 12150 12262`).
- From x 3056 the bullet needs about 256 frames to reach the pole base; Mario needs about 138. The
  wait is the bullet's speed, not the route.
- No other stompable enemy can reach that pole: the Buzzy Beetle (page 11 col 13) and the
  Paratroopa (page 12 col 11, on the pillar) are cut off by the pit and the 8-high wall at page 12
  cols 14–15 (`python3 tools/area_data.py L_GroundArea19 E_GroundArea19`).

This matches the community record ("better spawn proven to not be possible by using cheat",
`docs/community-claims.md`). Nothing stays open in this family.
