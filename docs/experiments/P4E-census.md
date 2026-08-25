# E9a — the wall-face census, static half (H46)

**Unit:** E9a. **Declared/done:** 2026-08-25 (session 19). **Acceptance:** every wall face on the
route classified, with the shortlist that goes to E9b. **Artifacts:** `runs/E9a/census.txt`,
`runs/E9a/loss_map.txt`, `runs/E9a/obstacle_cost.txt`, `data/blockmaps/*.{txt,grid,log}`.
**New tools:** `tools/route_blockmaps.py`, `tools/wall_face_census.py`, `tools/route_loss_map.py`,
`tools/route_obstacle_cost.py`. No emulator, no compute — disassembly plus `data/wr/fceux_wr.ram`.

---

## 0. One-paragraph summary

The census is **negative for its own primitive and positive for something else**. Every wall face on
the route — 708 of them across 14 areas — **refuses a static walk-through at both hitboxes**: the
only metatile that could hold the door open is a hidden block (`$5f`/`$60`), all nine on the route
are isolated in empty space, and **coins cannot do it at all** (the right probe collects them eleven
pixels before the left probe would need them, which is exactly why the WR's own 4-2 entry costs 31
frames). But the value map built to *prioritise* the census — pricing every off-cap stretch of the
WR against the 2.5 px/frame movement bound — found that the route's whole geometric loss is **290
frames**, and that **114 of them (39 %) sit at one previously unpriced place: 8-2's columns 201-212**,
where HappyLee wall-jumps up a two-column shaft. That site is not a clip problem. It is a jump-arc
problem, and it misses being a plain jump by about **one to two pixels of horizontal budget**.

---

## 1. The mechanic, exactly

Read out of `data/disasm/smbdis.asm`: `PlayerBGCollision` 11902-11960, `DoFootCheck` 11975-12021,
`DoPlayerSideCheck` 12022-12060, `CheckSideMTiles` 12063-12078, `ImpedePlayerMove` 12318-12351,
`BlockBufferCollision` 13053-13090, the adder tables at 13030-13041.

### 1.1 Which cells are probed

`ChkCollSize` picks the block-buffer adder base `$eb` from `BlockBufferAdderData = [$00,$07,$0e]`:
`$00` big-on-land, `$07` big-swimming, `$0e` **small OR crouching** (so a crouching big Mario gets
the small hitbox). `BlockBuffer_X_Adder`/`_Y_Adder` repeat in groups of seven, and the side check
probes `$eb+3, $eb+4` in its first iteration and `$eb+5, $eb+6` in its second:

| hitbox | head | feet | iteration 1 (counter `$00` = 2) | iteration 2 (counter `$00` = 1) |
|---|---|---|---|---|
| big (`$eb`=0) | (X+8, Y+4) | (X+3, Y+32) (X+12, Y+32) | (X+2, Y+8) **and** (X+2, Y+24) | (X+13, Y+8) **and** (X+13, Y+24) |
| small (`$eb`=14) | (X+8, Y+18) | (X+3, Y+32) (X+12, Y+32) | (X+2, Y+24) **twice** | (X+13, Y+24) **twice** |

So iteration 1 is the player's **left** side and iteration 2 is his **right** side, and for small
Mario each iteration probes one cell twice — the "two halves" collapse.

Block-buffer indices: column = `(page*256 + X + xadder) >> 4`, row = `((Y + yadder) & $F0) >> 4 − 2`.

### 1.2 Why the left probe is a free pass

The loop **exits at the first probe that finds something**, and the counter it exits on is what
`ImpedePlayerMove` reads:

* `$00 = 2` (a left probe hit) → `RImpd` → `cpy #$01 / bpl ExIPM` → **moving right: nothing happens.**
* `$00 = 1` (a right probe hit) → `cpy #$00 / bmi ExIPM` → moving right: `Player_X_Speed := 0` and a
  1 px push left.

**While a left probe sits in a non-empty cell, a right-moving Mario is never impeded and the right
probes are never consulted.** That is the walk-through primitive (F80, and F239's 250 px of it in
4-2 at `Player_X_Speed` = 40).

### 1.3 Correction to H33: "solid" is the wrong classifier

H33 and F80 describe entry as needing "a non-solid-but-non-empty tile". `CheckForSolidMTiles`
(`SolidMTileUpperExt = $10/$61/$88/$c4` by quadrant) is a **head-bump** classifier — it is what
decides whether a bumped block bounces or plays the bump sound. It is not what the side check uses.
The side check blocks on **anything non-empty**, minus these escapes:

| metatile | what happens at a side probe | persistent? |
|---|---|---|
| `$00` | nothing found; the loop moves on to the next probe | — |
| `$5f`, `$60` hidden coin / 1-up block | `ChkInvisibleMTiles` → `ExCSM`: **no impede from either side** | **yes** — only a head bump from below reveals it |
| `$c2`, `$c3` coin | `HandleCoinMetatile`: no impede, **cell erased to `$00`** | no |
| `$67`, `$68` jumpspring | `ExCSM` only while `JumpspringAnimCtrl != 0`, else `StopPlayerMove` | conditional |
| climbable (`>= $24/$6d/$8a/$c6`) | `HandleClimbing` | n/a |
| `$1c`, `$6b` pipe tops | skipped by the *first* sub-check only, then re-probed by `BHalf` | n/a |
| everything else | `StopPlayerMove` → `ImpedePlayerMove($00)` | — |

Two consequences that matter, and neither was on the board before:

1. **Every non-solid non-empty metatile in SMB1 is also non-climbable.** Non-solid values are
   `$01-$0F`, `$40-$60`, `$80-$87`, `$C0-$C3`; the climb thresholds all sit above them. So for small
   Mario the left-probe free-pass test is exactly `metatile != 0` — nothing subtler.
2. **The bricks the WR walks through in 4-2 are not "solid" by `CheckForSolidMTiles` at all**
   (`$52` < `$61`). F239's walk-through is not a solid-block phenomenon; it is a *non-empty*-block
   phenomenon, and the class is much wider than "bricks".

### 1.4 Why a coin can never open a face (this is F93's missing 'why')

Let a blocking run start at column `a`, so `(row, a−1)` is not blocking. The right probe enters
column `a` at `x = 16a − 13`; the left probe enters it at `x = 16a − 2`. **The left probe sits in
column `a−1` for the whole 11 px in between** — four to five frames at the 2.5 px/frame cap. So the
tile at `(row, a−1)` must be non-empty *and survive those frames*.

A coin does not survive: the **right** probe enters column `a−1` eleven pixels before the left one
does and collects it (`CheckSideMTiles` → `HandleCoinMetatile` → `ErACM` writes `$00`). By the time
the left probe arrives the cell is empty. This is exactly 4-2's `(29,10)` coin — three coins at
columns 27/28/29 in front of the brick run at 30-47, and the WR still had to pay **31 frames** of
`Player_MovingDir`-LEFT foot drift (F93) to cross those 11 px. The census now explains that price
rather than recording it.

**Only `$5f`/`$60` are non-empty, never-impeding and never consumed. They are the only static key.**

### 1.5 The general entry primitive is vertical, not lateral

`ChkFootMTile` ends with `lda Player_MovingDir / sta $00 / jmp ImpedePlayerMove` — a **`jmp`**, so
`ImpedePlayerMove`'s `rts` returns to `PlayerBGCollision`'s caller and **`DoPlayerSideCheck` never
runs that frame**. A frame in which the feet are in a non-empty cell with `Player_Y_Position & $0F
>= 5` therefore has **no side collision at all**, and if `Player_MovingDir` is LEFT while
`Player_X_Speed >= 1` it has no foot collision either. That is the mechanism behind F93, stated
generally: the way into a wall is to **sink into its top** with MovingDir LEFT, not to walk into its
face. Two further total-skip conditions from the same routine, recorded for the ledger:
`Player_Y_Position >= $cf` skips **all** of `PlayerBGCollision`, and `Player_Y_Position < $08` makes
`DoPlayerSideCheck` leave before any probe (`BHalf: cmp #$08 / bcc ExSCH`).

---

## 2. The block maps

`data/blockmaps/` held only 4-2. `tools/route_blockmaps.py` rebuilds every route area from
`data/wr/fceux_wr.ram` (wrapping `tools/blockmap_from_dump.py`, merging repeat visits), using the
area-load boundaries from `tools/slack_table.py`:

| tag | area | dump rows | columns read |
|---|---|---|---|
| `w11` | 1-1 main | 43-612, 927-1944 | 0-75, 160-217 (76-159 is the stretch the bonus room skips) |
| `w11b` | 1-1 bonus room | 613-926 | 0-23 |
| `w12` | 1-2 main | 2444-3814 | 0-199 |
| `w41` | 4-1 | 3815-6042 | 0-245 |
| `w42m` | 4-2 main | 6542-7220 | 0-99 |
| `w42w` | 4-2 warp zone (`$2F`) | 7221-7771 | 0-71 |
| `w81` | 8-1 | 7772-10813 | 0-395 |
| `w82` | 8-2 | 10814-12956 | 0-231 |
| `w83` | 8-3 | 12957-15057 | 0-235 |
| `w84r1..r5` | 8-4's five rooms | 15058-17868 | 0-95, 112-169, 192-231, 0-79, 256-309 |

Control: `w42m` columns 0-97 are **byte-identical** to the previously committed `w42_main.txt`.
The two pipe-intro areas (1-2 @1945, 4-2 @6043) produce no map and need none — F226: the joypad is
overridden for all 499 frames.

---

## 3. The census result

`tools/wall_face_census.py`. A *face* is the left end of a maximal run of blocking cells in one row.

| area | faces | refuses | admits (hidden block) | coin-dead | on the WR's own probe cells |
|---|---|---|---|---|---|
| w11 | 34 | 34 | 0 | 0 | 7 |
| w11b | 15 | 15 | 0 | 0 | 3 |
| w12 | 126 | 122 | 0 | 4 | 5 |
| w41 | 51 | 51 | 0 | 0 | 7 |
| w42m | 41 | 40 | 0 | 1 | 4 |
| w42w | 39 | 39 | 0 | 0 | 4 |
| w81 | 135 | 135 | 0 | 0 | 11 |
| w82 | 106 | 106 | 0 | 0 | 11 |
| w83 | 53 | 53 | 0 | 0 | 6 |
| w84r1-r5 | 108 | 108 | 0 | 0 | 19 |
| **total** | **708** | **703** | **0** | **5** | **77** |

**Zero faces on the route admit a static walk-through.** The five non-empty left neighbours are all
coins — four in 1-2 (row 6, columns 41/46/62-63/69, none on the WR's line) and 4-2's own at
(10, 29) — and §1.4 shows a coin is collected before it can help.

All nine hidden blocks on the route are **isolated**: empty cell to the left, to the right and below.

| area | row | col | value | left | right | below |
|---|---|---|---|---|---|---|
| w11 | 6 | 64 | `$60` | `$00` | `$00` | `$00` |
| w41 | 3 | 92 | `$60` | `$00` | `$00` | `$00` |
| w42m | 5 | 64 | `$5f` | `$00` | `$00` | `$00` |
| w42m | 6 | 63 | `$5f` | `$00` | `$00` | `$00` |
| w42m | 6 | 65 | `$5f` | `$00` | `$00` | `$00` |
| w42m | 7 | 66 | `$5f` | `$00` | `$00` | `$00` |
| w81 | 6 | 80 | `$60` | `$00` | `$00` | `$00` |
| w81 | 7 | 158 | `$5f` | `$00` | `$00` | `$00` |
| w84r2 | 7 | 150 | `$5f` | `$00` | `$00` | `$00` |

### 3.1 The big-Mario half (F238's untested geometry)

Big Mario's left probe covers **two** rows, so a face at `(r, a)` has two extra geometries: he
stands one row lower (probes `r−1, r`, free iff `grid[r−1][a−1] != 0`) or one row higher (probes
`r, r+1`, free iff `grid[r+1][a−1] != 0`). The tool finds **180 such face/mode pairs** — but every
one of them **reduces, not resolves**: the cell that would hold the door open is itself part of a
blocking run at that row, so the question just moves to *that* run's own left face. Following the
chain always terminates in an empty cell. **Big Mario adds no static entry anywhere on the route.**
What he does add is a strictly *larger* blocked profile (two right probes instead of one), so where
small Mario walks through, big Mario may not — the direction of the difference is against us.

**H46's static half is therefore closed with an empty census at both hitboxes.** Its dynamic half
(E9b) is not: §1.5's sink-entry is real, is what the WR itself uses in 4-2, and is invisible to a
static map because it depends on `Player_Y_Position & $0F`, `Player_MovingDir` and the arc.

---

## 4. The value map — which faces are worth anything

A walk-through only buys frames where the route is **off the movement cap**: SMB1's airborne x-speed
cap equals its ground cap, so clearing a short obstacle by jumping is free. `tools/route_loss_map.py`
joins the cap survey (F225) to the block maps; `tools/route_obstacle_cost.py` merges nearby off-cap
runs into obstacle windows and prices each against 2.5 px/frame.

**1,104 off-cap control frames on the route. Priced against the bound: 613 frames, of which 324 are
the forced post-card acceleration ramps (F225 — sixteen of them, ~18-40 frames each, unrecoverable)
and 290 are geometry.** The whole geometric loss of HappyLee's run is those 290 frames:

| loss (f) | area | dump rows | frames | x | cols | what it is |
|---:|---|---|---:|---|---|---|
| **114** | w82 | 12276-12458 | 183 | 3228→3401 | 201-212 | **8-2's shaft: the wall-jump climb. §5.** |
| 38 | w84r3 | 16492-16541 | 50 | 3427-3457 | 214-216 | 8-4 room 3's turnaround (H25, worked: F125/F133) |
| 33 | w42m | 6751-6843 | 93 | 383→532 | 23-33 | 4-2's col-30 wall entry (F93 — the 31 frames buy the warp key, so not a pure loss) |
| 33 | w12 | 3550-3628 | 79 | 2622→2737 | 163-171 | 1-2's endgame clip (F143/F144; E7/E11 running) |
| 30 | w42w | 7636-7681 | 46 | 918-958 | 57-59 | 4-2 warp-zone drop (H35: bound 461 vs WR 476) |
| 27 | w12 | 3708-3746 | 39 | 2913-2944 | 182-184 | 1-2's turnaround onto the warp pipes |
| 15 | w84r2 | 16158-16184 | 27 | 2405-2435 | 150-152 | 8-4 water room's exit pipe |

Read the other way: **8-1, 8-3, 4-1 and 1-1 contribute no priced geometric loss at all** — consistent
with F225, and it means those levels' deficits cannot be attacked by geometry of any kind.

---

## 5. The finding: 8-2's columns 201-212 cost 114 frames and nobody had priced them

### 5.1 The terrain (`data/blockmaps/w82.grid`, columns 190-208)

```
 r3-r5                                    61 61        <- the wall, cols 206-207
 r6-r7                          61        61 61        <- the pillar, col 203
 r8              61        61   61        61 61
 r9              61   61 61 61  61        61 61        <- staircase, cols 199-201
 r10             61   61 61 61  61        61 61
 r11    54 54 54 54 54 54 54 54 54 -- 54 -- -- 54 54   <- floor, pits at cols 202/204/205
 r12    54 54 54 54 54 54 54 54 54 -- 54 -- -- 54 54
 cols   190      197   199 200 201 202 203 204 205 206 207 208
```

A three-step staircase (cols 199-201, top row 8), a one-pit gap, a **one-column pillar at col 203
whose top is row 6** (standing `Y` = 96), a **two-column bottomless shaft at cols 204-205**, and a
**two-column wall at cols 206-207 running from row 3 to row 12** (standing `Y` = 48). The flagpole is
at col 216.

### 5.2 What the WR does (`data/wr/fceux_wr.ram` rows 12276-12470)

He lands on the pillar at x 3258, y 96, runs off its right edge, **falls into the shaft to y 192**,
and then **wall-jumps between the col-203 pillar and the col-206 wall** — the speed trace
`+24 → −3 → −24 → +2 → +24 → 0 → …` is `ImpedePlayerMove` zeroing him against alternating faces —
rising y 192 → 152 → 80 → 48, standing on the wall top at x 3295-3314, then jumping to y 12 and
falling to the floor at col 213. **183 frames for 173 px.** The bound is 69. **Loss 114 frames** —
five and a half framerules on a level whose deficit is 19 (`tools/slack_table.py`: 8-2 `w`=2).

### 5.3 It is not a clip candidate — it is a jump-arc candidate

The wall's face refuses at every row (col 205 is empty top to bottom), and §1.5's sink-entry needs a
foot over col 206, i.e. `x >= 3284`; but the side probe impedes from `x = 3283` unless the side row
is already above the wall's top (`Y <= 55`), at which point Mario is over it anyway. **So no
walk-through exists here at either hitbox.** The real question is the jump:

* the right side probe is inside the wall's columns for `x ∈ [3283, 3314]`;
* it clears if the side row is ≤ 2 throughout, i.e. **`Y <= 55`**;
* so a jump from the pillar (`Y` = 96) must gain **41 px of height in the `Δx` available before
  x = 3283**;
* the WR's own full-speed A-held arc, measured off his 8-2 jump at row 12252, rises
  38 px at `Δx` 22, **42 px at `Δx` 25**, 45 at 27, 48 at 30, 71 (apex) at 55;
* so the jump must be issued at **x ≤ 3259**;
* he is grounded on the pillar for `x ∈ [3236, 3260]` (`DoFootCheck` takes either foot: `x+3` or
  `x+12` inside col 203), but he **lands at x 3258**, and the earliest frame a jump can be issued is
  the frame *after* `LandPlyr` fires — by then `x ≈ 3260`.

**The direct jump over the wall misses by one to two pixels of horizontal budget.** That is a
sub-pixel/approach-arc question, not a physics wall: land on the pillar 3-10 px earlier and the same
arc clears with 10-25 px of margin (`Δx` 31 → rise 49 → `Y` = 47). Landing earlier means a flatter
approach jump out of x 3161, which must still clear the col-199/201 staircase (top row 8, `Y` = 128;
the WR passes it at y 126 with 2 px to spare) — so the two constraints fight, and which wins is
exactly what a local search rooted at x ~3160 settles.

**Caveats, stated so E9b does not inherit a false premise.** The arc was transcribed from one WR
jump, not re-derived from `JumpMForceData`; that jump is at speed 40 and the pillar jump would be at
39; the "cannot jump on the landing frame" step is a code-reading claim about the order of
`PlayerCtrlRoutine` and `PlayerBGCollision` within a frame; and the approach jump's own arc is
constrained by the staircase and by the enemies live in the region (`Enemy_ID` `$33` bullet bills
from the col-191 cannon, and a `$00` green koopa). **None of the 114 frames is claimed as available
until a core replay produces a path.**

### 5.4 Why the running finder has not found it

`runs/E8-w82/climb.log` is rooted at core 12240 with an 800-frame horizon over exactly this region
and is 6,900 s in with `best = 12953` (the control) and `goals = 1`. Its cell key is
`--xcell 6 --ycell 12 --spdcell 8` with **no subpixel dimension** — the same defect the Mac session
found for 1-2's clip, which is why `e7-sub16`/`e7-sub32` were relaunched with `--subcell`. A 1-2 px
landing question is invisible to a 6 px x-cell and a 12 px y-cell. **The 8-2 relaunch wants
`--subcell`/`--ysubcell` and a root at the approach jump (core ~3157 equivalent, dump 12160), not at
12240.**

---

## 6. Shortlist for E9b

Ranked by priced value. Every entry is a *rooting* problem — the reason none of these has been tested
is that reaching them means searching your way there first (H46), which `--root-state` fixes.

| # | site | value | what E9b must test | hitboxes |
|---|---|---|---|---|
| **1** | **8-2 cols 201-212** (`w82`, dump 12276-12458) | **114 f** | Not a clip. Root on the floor at x ~3150 and sweep the approach jump for a pillar landing at x ≤ 3252 with speed ≥ 39, then the direct jump over cols 206-207. Needs `--subcell`. | small (WR's) |
| 2 | 8-4 room 3 cols 214-216 | 38 f | Already H25/P2.2a′; the census adds nothing new — its faces all refuse. Keep as is. | small |
| 3 | 1-2 cols 163-171 | 33 f | The one place the route already enters terrain. §1.5 says the entry is a *sink* with MovingDir LEFT; test whether a sink that keeps `Player_X_Speed` exists (F239's "worth ~13 frames of overshoot"). `e7-sub16/sub32` are on it. | small, **and big** |
| 4 | 4-2 warp zone cols 57-59 | 30 f | H35's 15 frames are in the drop/fall/landing; faces refuse, so this is arc work, not clip work. | small |
| 5 | 1-2 cols 182-184 | 27 f | The turnaround onto the warp pipes — a deceleration, no face involved. Lowest clip prior of the set. | small |
| 6 | 8-4 room 2 cols 150-152 | 15 f | The exit pipe (`$10`/`$11` at rows 4-5); pipe faces refuse, and `$1c`/`$6b` tops are re-probed by `BHalf`, so no free pass. Arc work. | small |
| — | 4-2 cols 23-33 | (33 f, spent) | F93's entry is *bought*, not lost — it mints the warp key. Do not "recover" it. | — |

**What E9b should NOT spend time on:** enumerating more faces. The static census is complete and
empty. E9b's `--root-state` work should go straight to items 1 and 3, because those are the only two
sites where the priced loss is large **and** the mechanism is still open.

---

## 7. Status changes this unit makes

* **H46 static half: closed, empty at both hitboxes** (§3). The dynamic half stays open and is E9b.
* **H33's entry list is corrected** (§1.3/§1.4): "non-solid-but-non-empty" is the wrong test, coins
  and pipe-tops are not entries, climbable is a different outcome, and `$5f`/`$60` are the only
  static key — all nine of which are isolated.
* **New:** the route's total geometric loss is 290 frames and it is now localised and priced (§4).
* **New:** 8-2's 114-frame site (§5), the largest single geometric loss on the route, previously
  unpriced and mis-targeted by the running finder.

---

## 8. POSITIVE CONTROL — does the classifier reproduce a clip anyone has actually done? (F246)

Added after the user asked the right question: *a census that cannot reproduce known clips is
worthless.* `tools/clip_control.py` recomputes the §1.1 probe cells for every control frame of the
WR and flags every frame a probe is inside a blocking cell. Ground truth is HappyLee's own run,
which contains three publicly-known clips.

**272 embedded control frames in 14 episodes**, and the two long ones are exactly the known clips:
**4-2 rows 6786-6936 (151 f, x 468-764, probe rows 8/9/10)** and **1-2 rows 3572-3665 (94 f,
x 2676-2829, probe rows 2/3)**. The other twelve episodes are 1-5 frames and are ordinary impedes
(standing against a flagpole base or a face), not clips.

**1-2's clip, frame by frame, against the model:**

| frame | x | Y | spd | MDir | what the model says |
|---|---|---|---|---|---|
| 3571 | 2674 | 55 | **40** | R | both probes in col 167, empty — free |
| 3572 | 2676 | 54 | **0** | R | right probe (x+13) enters col 168 `$14` → `$00`=1 → **speed 0, 1 px push left** (§1.2) |
| 3573-3585 | 2677→2685 | 54-62 | 0 | **L** | `Y & $0F` = 6,6,7,9,11,13 — all ≥ 5, right foot in `$14` → **§1.5's `jmp ImpedePlayerMove` with MovingDir LEFT: +1 px/frame, side check never runs** |
| 3586 | 2686 | 62 | 0 | L | **left probe crosses into col 168** — 14 frames to cross the 11 px of §1.4 |
| 3587+ | 2686→ | 64 | 1,3,4,5,6… | R | inside: every frame a free pass, speed re-accelerates |

The model reproduces it exactly — the impede, the MovingDir flip, the +1 px drift, the nybble
condition, and the precise frame the left probe crosses. 4-2's entry has the identical signature
(airborne at speed 40, speed → 0 the frame the right probe touches the face; F93).

**So §3's negative must be stated more precisely, and this is the corrected claim:**

> **No face on the route admits a *full-speed* lateral entry.** Every clip that actually happens
> pays 40 → 0 → re-accelerate. That is not a footnote — it is *why* 1-2's clip costs 33 frames and
> 4-2's costs 31 in §4's table.

---

## 9. The 8-2 site, taken to the core — H48 confirmed as movement, refuted as a record (F247)

Direct probe rather than a search (`tools/w82_jump_probe.py`). **Control: the unmodified WR inputs
reproduce `StarFlagTaskControl == 5` at core 12952 and GES 5 at core 12472 exactly.**

**The jump works.** Splicing `A` into the WR's own inputs at core **12285** — the first frame after
the pillar landing at core 12284 — clears the wall: **x 3283 at Y 53** (needs ≤ 55), Y 40-48 across
both columns, **`Player_X_Speed` pinned at 40 the whole way**, on the floor at col 214 by core
**12348** against the WR's **12458**. §5.3's hand estimate that it "misses by 1-2 px" is **wrong**;
it clears by 2. That correction is the value of doing the replay instead of trusting an arc traced
off a different jump.

**And it is still not a record, for the reason doctrine says to check.** Every variant grabs the
flagpole with a **normal slide** (GES 4 → 5) at grab-Y 137-161, while HappyLee touches the pole at
**x 3443, Y 165-166** and goes **GES 8 → 5 in a single frame** with `StarFlagTaskControl` jumping
**0 → 2**, skipping task 1 entirely. Measured: best probe `$0746 == 5` at core **13015 (+63)**,
typical **13078 (+126)** — the same +126 the E8 launcher header records from its own proxy-goal
trap. **Reaching the pole 112 frames early and ending the level 63-126 frames late is exactly the
F230/F237 failure mode**, and it was caught only because the goal was checked against the quantity
the record is measured in.

**What is left open, and it is a good open question.** The glitch window is a ~4 px band in
`Player_Y_Position` (161 reached, 165-166 needed) at the frame `x+13` crosses into column 216 — on
a line that arrives with **112 frames of slack**. That is a subpixel-and-hop-phase search, which is
precisely what `runs/E9b/launch*.sh` is configured for (`--subcell`, rooted at 12157).
