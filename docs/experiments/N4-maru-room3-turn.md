# N4 — Maru's 8-4 room 3 turnaround without Left+Right: is one frame there?

2026-11-10, Mac (QuickNES core 26bb785, `build/endlab`). Movie: `runs/N1-ending/maru_inputs.bin`
(from `data/wr/maru-rtarules.fm2`, `--input-skip 2`). `E` below is
`build/endlab third_party/QuickNES_Core/quicknes_libretro.dylib roms/smb.nes runs/N1-ending/maru_inputs.bin --input-skip 2`.

## Question

Maru enters room 3's pipe with Down on core 16554 at x 3403.44. One frame earlier he is at
3405.94; the pipe takes x pixel 3396–3404, so he is 0.94 px short (F313). Room 3 was the one room
of his 8-4 that had not been searched. A pipe entry on core 16553 would be a new record by axe
time in the no-Left+Right category, provided the later rooms can be re-solved one frame earlier.

## His line (`E --trace 16494 16556`)

| core | what happens |
|---|---|
| 16496–16503 | Left in the air: braking 1.78 units per frame (doubled, the speed byte is ≥ 25) |
| 16504 | lands, speed 24 |
| 16505–16513 | Left+B on the floor: skid, 1.625 per frame, down to speed 10 at x 3456.06, ScreenLeft 3344 |
| 16514 | `ProcSkid` (speed byte < 11): instant stop |
| 16515 | Right on the floor: sets facing right |
| 16516 | takes off with Right: speed +2, crosses pixel 3456, ScreenLeft 3345 (the scroll is done) |
| 16517–16535 | Left in the air: 1.625 per frame (doubled, facing right against moving left) up to the air cap 24 at 16534 |
| 16536 | lands |
| 16537 | one floor frame: speed 26 (doubled once; makes the speed byte ≥ 25, which lifts the air cap to 40) |
| 16538 | jumps; 0.89 per frame in the air |
| 16547 | first frame with x < 3422: passes the pipe's corner at y 87, side point 1 px above the pipe top |
| 16551 | lands on the pipe top (y 80), speed 39 |
| 16554 | Down at x 3403.44 |

## Why the frame is not there (hand analysis)

1. **The corner.** On 16546 he is at x 3422.44 with y 89, still below the height that clears the
   pipe. He may not be left of 3422.0 before y ≤ 87, so only 0.44 px is free there.
2. **Speed at the corner.** He passes it at speed 35 and reaches 40 on 16553. Passing it at 40
   would enter on 16553. The second jump accelerates at 0.89 per frame because facing equals moving
   direction; doubling it needs a floor frame with Right first, which delays the jump one frame.
   Net zero.
3. **Taking off earlier.** The chain from the first take-off is fixed: hop 20 frames (the shortest
   hop), one floor frame, jump, 9 frames to the corner, 7 to the pipe = 38. An earlier take-off
   needs the instant stop one frame earlier, which needs speed ≤ 10 on 16512; it is 11. Braking one
   frame sooner costs 1.9 px of position, so he would need a 2.46 px lead entering the braking. The
   known lead is 0.31 px (F313).

## Search record

`endlab --turn F0 D [--beam K]`: every no-Left+Right input from core F0 (12 pads on the floor,
plus Down pads when standing high; A/L/R rising, L/R falling), dedup per frame on the full gameplay
key, goal = vertical pipe entry with ScreenLeft ≥ 3345 on a frame ≤ D. A node is dropped when it
cannot reach x 3404 by D even accelerating left at 1.79 per frame every frame (admissible). With
`--beam K` only the K best nodes (lowest projected x) are kept per physical bucket (floor/air,
height, vertical speed, facing, moving direction, speed byte ≥ 25, scroll done, jump force, A held,
running flag); that part is a heuristic.

| run | result |
|---|---|
| control: `E --turn 16513 16554 --beam 12` | 96 entries on core 16554 at x 3403.438, area pointer `$02`; 443,208 steps, 22 s |
| `E --turn 16494 16553 --beam 16` | frontier dead on core 16524; 179,241 steps |
| `E --turn 16494 16553 --beam 200` | frontier dead on core 16546, best x 3423.25 on that frame; 8,705,520 steps, 420 s |
| `E --turn 16494 16553` (no beam) | 1,986,904 nodes on core 16509, stopped: too big to finish |
| `E --turn 16460 16553 --beam 48` | see STATUS (run last) |

The wide beam dies exactly at the corner of step 1: its best node on 16546 is at 3423.25, right
of Maru's 3422.44, and no kept node can still reach the pipe by 16553.

## Conclusion

No pipe entry on core 16553 was found, and the hand analysis says why. This is a beam-level
negative plus a structural argument, **not a proof**: the search without a beam does not finish,
and the starts tested are Maru's own states at core 16494 and 16460. What would overturn it: a
2.46 px lead into the braking, a wall right of x 3457 to stop against, or a way to reach speed 40
by the corner.
