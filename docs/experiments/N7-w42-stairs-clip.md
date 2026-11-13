# N7 — 4-2 warp zone: clip through the staircase instead of going over the roof (2026-11-12, Mac)

User idea from the route viewer: the warp-zone area is entered at x 24, and the record climbs the 9-column
staircase (cols 40-48, rows 3-10, metatile $61), runs along the one-tile roof (row 2, cols 48-59), drops
through the gap at cols 60-61 and comes back 150 px to the world-8 pipe (cols 50-51, x 804-812). Could Mario
go through the staircase and come out beside that pipe? The record already runs inside 4-2's brick row at
full speed (F246), so the traversal is not the question; getting in is.

## 1. The warp still needs x 880 (measured + code)
`WarpZoneControl` ($06D6) is written by the area parser's `ScrollLockObject_Warp` (smbdis 3566) when its column
is parsed. In the record that is core 7604: x 882, ScreenLeft 770, `$06D6` 0 -> 6, `ScrollLock` 0 -> 1.
`HandlePipeEntry` (12288) changes the world only if `$06D6` != 0. So any route must put Mario at x >= 880
(ScreenLeft 768 = x - 112) and return to x 804-812. The record takes 116 frames from that frame to its pipe
entry (7720); a floor-level return from x 880 is about 47-60 frames by arithmetic (not built).
Gross saving of a through-the-stairs route: about 55-70 frames before the cost of getting in.

## 2. A speed-keeping entry does not exist (code + poke test)
F244's free frame (feet >= 5 px into a tile, moving direction LEFT, x speed >= 1) cannot occur moving right:
`ChkMoveDir` (smbdis 5599-5604) rewrites `Player_MovingDir` from the sign of `Player_X_Speed` every frame,
immediately before `PlayerBGCollision`; it is left alone only when the speed is exactly 0. With speed >= 1 the
foot impede takes the direction-1 branch: speed := 0, x -= 1.
Poke test (`tools/clip_poke_lab.py runs/N7-w42-stairs/wr_inputs.bin 7527 7527 96 112`): at the col-44 face,
x 689, speed 40, poked moving direction 2 and y 96..112, no input. y 96-100 lands on the block; **y 101-112
(feet 5+ px in): speed 40 -> 0 on the first frame and x 691 -> 690** in every case.

## 3. The slow entry needs a block overhead, and the steps have none
The only way in is the record's own (4-2 main, cores 6782-6800): hit the face (speed 0), one Left frame
(speed -1 -> moving direction 2), then +1 px on every falling frame whose feet are 5-15 px into the face
tile; a landing frame gives -1. The record gets 18 such frames in a row because the brick above his head
(row 9 over row 10) cuts each hop to 4 px (y 176/172/173/174/176). Every stair face is one tile high with
air above it (grid at core 7640 below), so a hop there is a full hop: measured 20 frames in the air from
the step (script in the log), of which at most 3 fall through the 11-px window.
Estimate: about +2 px per 20-odd frames, 11 px to cross => of the order of 100 frames against the 55-70
it could save. **Estimate, not a search result.**

```
     40 41 42 43 44 45 46 47 48 49 50 51 52 53 54 55 56 57 58 59 60 61 62 63
r 2   .  .  .  .  .  .  .  . 61 61 61 61 61 61 61 61 61 61 61 61  .  . 61 61
r 3   .  .  .  .  .  .  . 61 61  .  .  .  .  .  .  .  .  .  .  .  .  . 61 61
r 4   .  .  .  .  .  . 61 61 61  .  .  .  .  .  .  .  .  .  .  .  .  . 61 61
r 5   .  .  .  .  . 61 61 61 61  .  .  .  .  .  .  .  .  .  .  .  .  . 61 61
r 6   .  .  .  . 61 61 61 61 61  .  .  .  .  .  .  .  .  .  .  .  .  . 61 61
r 7   .  .  . 61 61 61 61 61 61  .  .  .  .  .  .  .  .  .  .  .  .  . 61 61
r 8   .  . 61 61 61 61 61 61 61  . 10 11  .  . 10 11  .  . 10 11  .  . 61 61
r 9   . 61 61 61 61 61 61 61 61  . 14 15  .  . 14 15  .  . 14 15  .  . 61 61
r10  61 61 61 61 61 61 61 61 61  . 14 15  .  . 14 15  .  . 14 15  .  . 61 61
```

## 4. Searches attempted (none finished; all exploded)
`endlab --flag` with new options `--through X Y` (clip probe), `--clip/--clipfrom`, `--airfull`, `--pickfloor`,
`--boxy`, `--xmax`. Whole-approach runs from core 7440 passed 100k nodes within 15 frames; boxed runs from a
single state on step 42 (`on_step42.bin`, x 667 on core 7518) passed 1.2-2 M nodes within 9-15 frames with
16, 8 and 4 pads (`c_step43.log`, `e_step43_box.log`, `f_step43_box4.log`). The player-physics key is too
fine for a blind search here; a model search (smb-opt, with a "left probe inside cols 43-48" goal) would be
the sound test.

## Status
Not viable by the known mechanism; not refuted. Would be overturned by: a way to hold speed 0 with moving
direction 2 through 11 consecutive falling frames at a one-tile face (a slower fall), any non-empty tile over a
stair face (a kicked shell or a bounced block is not available here: the area has no enemies and $61 does not
bounce), or an entry primitive other than F244's.
