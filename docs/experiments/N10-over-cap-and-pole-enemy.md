# N10 / L10b — the one ingredient every near-miss lacks, asked of the game directly (2026-11-13/14)

Every near-miss on the board needs a single frame in which Mario moves more than the 2.5 px the speed cap
allows: F316 3.06 px (castle-walk skip, 1-1 / 4-1 / 8-1, 126 frames each), F324 3.2 px (8-3 glitch grab, 42
frames), F318 / F334 2.75 px (1-1 castle walk, 21 frames). The other way to the 8-3 grab is an enemy to bounce
off at the pole, which is how the WR's own 8-2 ends (stomp on core 12468, y speed -3, grab on 12472).

**Verdict: dry on both. Rollout-policy negatives, one seed per root (two for L10b), not proofs.** One real side
finding in 1-1 (section 3).

## 1. L10b — an enemy at the 8-3 flagpole (Fedora box)

`runs/L10b-pole-enemy/launch.sh`, explore class 19 `stompable enemy at the flagpole` (a live enemy of id < $15
or a bullet bill within 80 px left / 16 px right of the live flag object). Controls on 8-2 from root 12300: silent
(calibrated off, the WR does it), fires with `POLE_NOCAL=1`. Six 6-h sweeps of 8-3, launched 2026-11-13 20:54 CST.

| root | start | rollouts | frames | class 19 hits | mask |
|---|---|---|---|---|---|
| whole_a / whole_b | 13110 (level start) | 8.81 M / 8.81 M | 193.43 M / 194.06 M | 0 / 0 | `0x14101` |
| koopa / koopa_b | 13900 (before the koopa at x 2192) | 8.85 M / 6.75 M | 192.04 M / 143.46 M | 0 / 0 | `0x14101` |
| hbros / hbros_b | 14200 (before the last hammer bros) | 9.63 M / 6.89 M | 202.98 M / 144.25 M | 0 / 0 | `0x14101` |

1.07 billion frames, every root reaches the pole (max x 3431), **no enemy ever within 80 px of it**. 8-3's roster
for reference (`E_GroundArea2`): paratroopas at x 480 and 1488, a green koopa at x 2192, hammer bros at x 1008,
1040, 1872, 1904, 2336, 2544, 2832, 2960; cannons at x 288, 544, 1376 (they keep firing all level; each bullet is
created at its cannon and erased the next frame).

## 2. N10 — over the speed cap (Mac)

`runs/N10-lead/launch_mac.sh`, two new explore classes:
- **21 `single-frame step over 40/16 px`**: x advanced 41-80 sixteenths in one frame, in control on both frames,
  same area. The WR's own largest step is exactly 2.5 px in all eight levels. Control: fires with `STEP_THR=39`,
  silent at 40.
- **20 `ahead of the cap line`**: x beyond the reference's best earlier position + 40/16 px per frame, the chain
  starting when the reference first reaches speed 40 in the area. Controls: silent on 4-2 (the WR waits at the
  mint) and at 8-1's end (the WR slows on purpose); fires inside the start ramp.

Six 3-h sweeps, launched 2026-11-13 21:56 CST.

| root | stretch | rollouts | frames | class 21 | lead in the ramp | lead after the WR is at top speed |
|---|---|---|---|---|---|---|
| w41 | 4-1 whole | 6.19 M | 159.55 M | 0 | 2/16 px (core 4004) | **0** |
| w81 | 8-1 whole | 6.56 M | 162.45 M | 0 | 2/16 (7956) | **0** |
| w83 | 8-3 whole | 6.55 M | 161.81 M | 0 | 2/16 (13145) | **0** |
| w82a | 8-2 to the wall | 6.49 M | 159.13 M | 0 | 2/16 (11002) | **0** |
| w11a | 1-1 room 1 | 6.48 M | 166.62 M | 0 | 2/16 (219) | **0** |
| w11t | 1-1 after the pipe | 7.13 M | 168.42 M | 0 | 5/16 (1078) | **5/16, persisting as 4/16** |

978 million frames. **No single frame over 2.5 px anywhere.** The 2/16 px in the level-start ramps does not
survive to top speed in any level.

## 3. The 1-1 tail: the WR carries a quarter pixel it does not use

Replayed `runs/N10-lead/anom_20_f1084.path` against the WR (same core, B+Right appended):

| core | WR x / speed | rollout x / speed | lead |
|---|---|---|---|
| 1074 | 2646.6875 / 35 | 2646.6875 / 35 | 0 |
| 1075 | 2648.875 / 35 | 2648.9375 / 36 | 1/16 |
| 1076 | 2651.125 / 36 | 2651.3125 / 38 | 3/16 |
| 1077 | 2653.5 / 38 | 2653.8125 / 40 | 5/16 |
| 1083 (landing) | 2668.5 / 40 | 2668.75 / 39 | 4/16 |
| 1084-1100 | speed 40 | speed 40 | 4/16 |

The WR's movie has one frame with no direction held while accelerating in the air (speed 35 on two consecutive
frames, cores 1074-1075). The rollout holds Left+Right+B through it and reaches 40 one frame sooner.

**It does not open 1-1.** Positions on the cap line step in sixteenths. The WR is at x 3155.9375 on core 1278,
the largest value still left of the base-block column (3156), which is what makes the next frame's entry as deep
as it can be (3158.4375). Any of the five spare sixteenths puts Mario at 3156.0 or more on 1278, so he enters a
frame sooner and shallower (at most 3156.25), and by F334's count ends at most at 3156.25 after landing against
the 3158.0 a grab needs. The released frame looks like deliberate tuning of that position. As time the lead is an
eighth of a frame.

## 4. What this leaves

- H47 (an over-cap displacement) has now been looked for by reading (F294/F295) and by watching: nothing on the
  flag levels. Not covered: 1-2, 4-2 and 8-4, and anything a random rollout does not stumble on.
- H57 (8-3 glitch grab) has neither of its two ways: no step over the cap, no enemy at the pole.
