# H12 — L+R beyond the reversal: an out-of-table ROM read, measured, and the clamp that eats it

**Unit:** H12 (`docs/open-threads.md`, structural long shots). Linux box, 2026-08-25 session 21.
Pure reading plus four 1,300-frame harness runs — no search, no RAM budget.

**Why this is not E10 ground.** E10 read the ROM for *what can write where* (arming ACE, corrupting
state) and closed that surface. It never looked at input semantics. `docs/input-semantics.md` (P0.7)
catalogued the ordinary paths but stopped at "L+R sets facing = 3, which doubles the friction adder"
— it never asked what *else* reads `PlayerFacingDir`, and 3 is a value no single button can produce.

## 1. The find: facing 3 indexes one byte past two tables

`PutPlayerOnVine` (smbdis.asm 12205) places the player on any grabbed climbable metatile:

```asm
SetVXPl: ldy PlayerFacingDir     ; 1 = right, 2 = left … or 3, which only L+R produces
         lda $06                 ; low byte of the block-buffer column address
         asl / asl / asl / asl   ; column → pixels within the page
         clc
         adc ClimbXPosAdder-1,y  ; ← 2-byte table
         sta Player_X_Position
         lda $06
         bne ExPVne              ; page adder only when the cell is buffer-1 column 0
         lda ScreenRight_PageLoc
         clc
         adc ClimbPLocAdder-1,y  ; ← 2-byte table
         sta Player_PageLoc
```

Both tables have two entries. `y = 3` reads the byte *after* each. Verified in the ROM image itself,
not just the listing — the byte string `f9 07 ff 00 18 22 50 68 90` occurs exactly once in
`roms/Super Mario Bros. (W) [!].nes`, at file offset `0x5e35` = **CPU $DE25**:

| symbol | CPU | bytes |
|---|---|---|
| `ClimbXPosAdder` | $DE25 | `f9 07` |
| `ClimbPLocAdder` | $DE27 | `ff 00` |
| `FlagpoleYPosData` | $DE29 | `18 22 50 68 90` |

So with facing 3: the X adder is `ClimbPLocAdder[0]` = **$ff**, and the page adder is
`FlagpoleYPosData[0]` = **$18** — `Player_PageLoc := ScreenRight_PageLoc + 24 pages = +6,144 px`.

**Why the flagpole is immune and the vine is not.** `FlagpoleCollision` does `lda #$01 / sta
PlayerFacingDir` before reaching this code, so the route's five flagpole grabs can never see it. The
`VineCollision` fall-through (`cmp #$26 / bne PutPlayerOnVine`) sets nothing — whatever the player is
facing is what indexes the table.

## 2. Measured on the real core (F268)

`tools/climb_facing_probe.py` — one command, no arguments. It plays the WR with Left+Right forced
from frame 1226 (1-1's staircase: facing becomes 3 while Mario is grounded, and stays 3 once he is
airborne, because only `OnGroundStateSub` and the swimming path write facing), pokes `$26` into every
column of the block-buffer row his side probe reads, and lets the grab fire at frame 1251 — chosen
because the probe there lands in **column 0 of block buffer 1**, the `$06 == 0` case that arms the
page adder. Facing is poked to 1 and 2 for controls: identical trajectory, identical cell, only the
index differs.

```
facing                   frame  face  state  page    X       x  no-poke x
3 (L+R, out of table)     1251     3      3    36  255    9471       3065
                          1252     3      2    11  138    2954       3066
1 (control)               1251     1      3    11  249    3065       3065
2 (control)               1251     2      3    12    7    3079       3065
```

The controls land exactly where the in-table bytes say (`$f9`/`$ff` → page 11 X 249; `$07`/`$00` →
page 12 X 7). **Facing 3 moves Mario from x 3063 to x 9471 in one frame — +6,406 px.** The mechanism
is real, it is driven by nothing but a button combination, and it is the first over-cap forward
displacement anyone on this project has produced (H47's premise).

## 3. …and it is undone on the very next frame (F269)

Frame 1252 puts him at x 2954 — *behind* where he started. The culprit is `ChkPOffscr`/`KeepOnscr`
(smbdis.asm 5428–5447), which runs every frame:

```asm
ChkPOffscr:   jsr GetXOffscreenBits       ; for the player
              ldy #$00                    ; default offset = left side
              asl
              bcs KeepOnscr               ; d7 set → clamp to the LEFT edge
              iny
              and #%00100000
              beq InitPlatScrl            ; no bits → no clamp
KeepOnscr:    lda ScreenEdge_X_Pos,y
              sbc X_SubtracterData,y
              sta Player_X_Position       ; "store as player position to prevent movement further"
              lda ScreenEdge_PageLoc,y
              sbc #$00
              sta Player_PageLoc
```

`GetXOffscreenBits` (14909) computes `ScreenEdge − object` as a 16-bit difference; a jump of +24
pages makes the high byte negative, which takes the `bmi XLdBData` path and returns bits with **d7**
set — so the clamp picks `y = 0` and snaps Mario to the screen's **left** edge.

**That makes the primitive a strict loss.** Mario is always on screen when he grabs, so
`ScreenLeft ≤ x ≤ ScreenRight`; the clamp therefore costs `x − ScreenLeft`, which is 0 at best and a
full screen width at worst. Measured here: 3065 → 2954, **−111 px ≈ 44 frames of running**.

And the general form is worth more than the specific one: **any horizontal teleport large enough to
set an offscreen bit is undone the next frame, in the direction the bits report.** A displacement
mechanism can only pay if it lands the player *within the current screen*. That is a real constraint
on H47 and on every future teleport idea, and it did not exist in the ledger before today.

## 4. How much room is there, and the variant that dodges the clamp (F270)

Two follow-ups, both measured.

**How much forward room the screen allows.** The furthest right the game permits is
`ScreenRight_X_Pos − 16` — that is `KeepOnscr`'s own right-edge case (`X_SubtracterData` =
`.db $00, $10`). Measured against the WR's own position over every control frame with
`Player_Y_HighPos` = 1:

| level | frames | min slack | median | max |
|---|---|---|---|---|
| 1-1 | 707 | 45 | **127** | 216 |
| 1-2 | 1270 | 111 | **127** | 199 |
| 4-1 | 1432 | 127 | **127** | 199 |
| 8-2 | 1461 | 124 | **127** | 199 |
| 8-4 room 1 | 523 | 127 | **127** | 199 |
| 8-4 Bowser room | 270 | 42 | **127** | 183 |

HappyLee runs a constant **127 px behind the maximum legal on-screen x** — about **50 frames** at the
2.5 px/frame cap. That is the ceiling on the whole H47 class, and it is far more generous than the
board assumed. It is also why §3's clamp is a *limiter*, not always a reset: a teleport that
overshoots the right edge comes back to `ScreenRight − 16`, which is still 127 px ahead.

**The variant that is never clamped.** The X adder is applied without touching `Player_PageLoc`
whenever `$06 != 0` (any column but buffer-1 column 0), so an in-page displacement raises no
offscreen bit at all. `ClimbingSub` (6006) writes `PlayerFacingDir := Left_Right_Buttons EOR $03`, so
**L+R while on a vine sets facing = 0**, and index 0 reads `ClimbXPosAdder-1` = **$8a**:

```
1-1 frame 427, probe column 4, --poke 0x33=0 :  x 583 → 714   (+131 px, slack −5, NO clamp)
                               control face 1:  x 583 → 569
                               control face 2:  x 583 → 583
```

So the placement `Player_X_Position := column*16 + $8a` is real and survives. **Why it still is not a
saving:** it is an *absolute* placement relative to the grabbed column and wraps mod 256 inside the
page, so the next frame's grab re-placed him (column 12 → x 586); and arming facing 0 requires a vine
to already exist — the route's vines are in 1-2 and 4-2, and **8-4, the level where one frame is the
record, has none.**

## 5. Verdict

- H12's vine/facing branch: **the mechanism exists, is worth up to ~50 frames by the F270 window, and does not pay on this route** — the +24-page form is clamped away and the unclamped +138 px form needs a vine, which 8-4 does not have. Not "no mechanism was found" —
  a measured mechanism, measured to be negative. Recorded as F268 (it exists) and F269 (the clamp).
- H47 is *not* satisfied by this: the displacement is real but self-cancelling.
- H14 (vine teleport skipping a section) is refuted **for this route into it** by the same clamp.

## 6. Still open in H12
1. **`Player_MovingDir` = 3** (`ProcSkid` sets moving := facing when |speed| < $0B). Checked at the
   sink site (`PlayerBGCollision` 12012 → `ImpedePlayerMove`): 3 takes the same branch as 2, and the
   frame's own `ChkMoveDir` (5598) rewrites MovingDir from the sign of the speed whenever the speed is
   non-zero — so at collision time MovingDir = 3 only ever coexists with speed 0. Bounded, no gain.
   The other MovingDir readers (6152, 6184, 6208, 9479 blooper, 14612) are unaudited.
2. **Swimming.** `input-semantics.md` §4 skips it on the stated premise "no water on the WR route".
   **That premise is false:** 8-4's water room is 696 route frames (F265, sub-area `r4`), 667 of them
   at the swim cap. The input semantics of the one place the route swims have never been read.

## 7. Reproduce

```
python3 tools/climb_facing_probe.py          # the table in §2; needs build/harness and the ROM
```

---

# L10 — the other nine `PlayerFacingDir` / `Player_MovingDir` readers (session 22)

**Unit:** L10, 2026-08-25 session 22, Linux. Pure reading — no search, no RAM, run while four jobs
were live. Method as in §1: find the site, decide whether the index can leave its table, and if it
can, check the table's real size in the listing and what sits after it.

`SetVXPl` / `PutPlayerOnVine` (§1) was the only one of eleven that had ever been checked, and it
produced F268's +6,406 px. These are the other nine.

## 8. The site table

| smbdis | routine | how facing / moving dir is used | out of range? | verdict |
|---|---|---|---|---|
| 5989 | `MoveOnVine` → `CSetFDir` | `ClimbAdderLow,x` + `ClimbAdderHigh,x`, X ∈ {0,1,2,3} built from (right-pressed, facing==1) | **No** | Both tables are **4 bytes** — `.db $0e,$04,$fc,$f2` and `.db $00,$00,$ff,$ff` — sized for exactly this 2×2. Facing 3 takes the same branch as facing 2. Vine-only, and 8-4 has no vine |
| 6152 | `X_Physics` | `cmp Player_MovingDir` — comparison, never an index | n/a | See §9: it is the *value* of `Player_MovingDir` that matters here, not a table |
| 6184 | `GetXPhy` | `MaxLeftXSpdData,y` (3 B, y≤2), `MaxRightXSpdData,y` (**4** B, y≤3 — the 4th is the pipe-intro `$0c`), `FrictionData,y` (3 B, y≤2); facing only in a `cmp` | **No** | All three in range; y comes from the 0–2 ladder or the explicit `ldy #$03`. The facing-3 friction doubling here is the already-known effect |
| 6208 | `GetPlayerAnimSpeed` → `ProcSkid` | `PlayerAnimTmrData,y` (3 B, y≤2) — in range — **but `lda PlayerFacingDir / sta Player_MovingDir`** | table No; **the write is the find** | **The one new primitive: `Player_MovingDir` can become 3.** Analysed in §9 |
| 6346 | `FireballObjCore` | `ldy PlayerFacingDir / dey / lda FireballXSpdData,y` → y = **2** | **YES** | `FireballXSpdData` is **2 bytes** (`.db $40, $c0`); index 2 reads the byte after it. A genuine second out-of-table read — but it only lands in `Fireball_X_Speed`, and it needs Fiery Mario, which this route never becomes. No player displacement |
| 6396 | `SetupBubble` | `lsr` on facing, tests d0 only | No table | Facing 3 has d0 = 1, so it takes the facing-1 branch. Air bubbles are cosmetic |
| 9479 | `MoveBloober` | `ldy Player_MovingDir` → `sty Enemy_MovingDir,x` | copies a 3 into an enemy field | The consumer (`SwimX`, 9495) is `ldy Enemy_MovingDir,x / dey / bne` — a test, not a table. 3 behaves as 2 (swim left). Chain dies here; see §9 |
| 12079 | `CheckSideMTiles` → `ChkPBtm` | `ldy PlayerFacingDir / dey / bne StopPlayerMove` | test only | **Constraint worth carrying: facing must be exactly 1 to enter a downward pipe.** Facing 3 (L+R) falls to `StopPlayerMove` — L+R *blocks* pipe entry. Directly relevant to L4 |
| 14612 | `ProcOnGroundActs` | `lda Player_MovingDir / and PlayerFacingDir` → skid graphics offset (y≤6) | No | 3 AND 1 = 1 → non-zero → no skid frame. Cosmetic |

## 9. The one new primitive, and why it defeats itself

`ProcSkid` (6217) is the **only** writer in the game that can put a 3 into `Player_MovingDir` — the
main writer, `SetMoveDir` (5604), only ever stores `$01` or `$02` (`lda #$01` … `asl`). Its
conditions are reachable: hold L+R (so `SavedJoypadBits & $03` = 3, which never equals a normal
moving direction, so the skid branch is taken) with `Player_XSpeedAbsolute < $0b`.

Two normally-adverse comparisons then flip to *equal*, and both are speed-relevant:

- **`X_Physics` (6152):** `lda Left_Right_Buttons / cmp Player_MovingDir / bne ChkRFast`. Holding L+R
  normally fails this compare (3 vs 1 or 2) and drops to `ChkRFast`, which increments Y and costs you
  the top cap. With `Player_MovingDir` = 3 it **matches**, keeping the path that can reach `GetXPhy`
  with **Y = 0** — `MaxRightXSpdData[0]` = `$28` = the 40 cap.
- **`GetXPhy` (6184):** `lda PlayerFacingDir / cmp Player_MovingDir / beq ExitPhy`. Facing 3 against
  moving dir 3 **matches**, so the `asl FrictionAdderLow` that doubles friction under L+R is skipped.

So the state cancels both known L+R penalties at once. It still does not pay, for a reason visible in
the same listing:

1. **The writer zeroes the speed in the same breath.** `ProcSkid` continues `lda #$00 / sta
   Player_X_Speed / sta Player_X_MoveForce`. You cannot enter the state with speed.
2. **It survives only at zero speed.** `SetMoveDir` runs every frame *after* `PlayerMovementSubs`, and
   `ldy Player_X_Speed / beq PlayerSubs` skips the store **only** when speed is exactly 0. The first
   frame the player has any horizontal speed, `Player_MovingDir` is overwritten with 1 or 2 and the
   state is gone.

Net: **at most one frame of favourable branches, bought with the player's entire horizontal speed.**
That is not a trade any route wants, and it is a code-level argument, not a search result.

## 10. Verdict

Eleven readers now audited, and **the vine remains the only one that reads past its table into
something that moves Mario.** One further genuine out-of-table read exists (`FireballXSpdData[2]`,
6346) but it is confined to a fireball's speed and needs a powerup the route never takes. Everything
else is either sized for the out-of-range value already (`ClimbAdder*`, 4 bytes), sanitised at the
consumer (`ImpedePlayerMove` does `ldx #$02`, so `$00` = 3 is identical to `$00` = 2 — worth knowing,
since that is the routine the whole clip programme lives in), a bit test that treats 3 as 1, or
cosmetic.

**Two things to carry forward:**
- **L4 constraint:** a downward pipe needs `PlayerFacingDir == 1` exactly (12079). Any candidate
  holding L+R at the pipe mouth is impeded instead of entering. Worth checking the model honours this.
- **Dead end recorded so it is not re-walked:** `HammerXSpdData` (6870) *is* a 2-byte table indexed by
  `Enemy_MovingDir − 1`, so a 3 there would read out of range — but the only path that copies
  `Player_MovingDir` into an enemy is the bloober (9479), and no Hammer Bro ever receives it.
