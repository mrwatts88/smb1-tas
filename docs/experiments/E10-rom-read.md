# E10 — the unaudited half of the ROM, read end to end

**Unit:** E10 (Track B, pure reading — `docs/open-threads.md` Tier 2 #3, "best expected value
per hour on the board"). Mac session, 2026-08-25.
**Input:** `data/disasm/smbdis.asm` (16,351 lines) read with the question *"what relationships
across routines has nobody chased?"*, cross-checked against the WR dump
(`tools/slack_table.py data/wr/fceux_wr.ram`), `docs/timing-model.md`, and the existing ledger.
**No compute.** Every claim below is either a dump measurement or a line-cited code argument.

This session started from a checkout five sessions stale (d679bb8) and did the read
independently; the reconciliation against F203–F251 is folded in below, and everything that
merely re-derives an existing fact has been dropped rather than restated. Three things survive
that the ledger does not have, and one of them closes the board's top open lead.

---

## 1. **H43(b) is refuted at code level: the player head bump can NEVER write out of bounds.**
### (and F210 / F216 are wrong — the guard they solved is not the binding one)

`docs/open-threads.md` #4 calls H43(b) — "a head bump at `Y + adder < $20` on an odd-page
column 11" — *"the single highest-leverage missing primitive in the project"*. F210 derives a
2-pixel window `Player_Y_Position ∈ {$FE, $FF}` for it; F216 extends the same derivation to big
Mario (rows $D0 from Y $EC–$FB, $E0 from Y $FC–$FF) and to big-crouching.

Both solve **`HeadChk`'s own guard** (11946–11948, `cmp PlayerBGUpperExtent,x`) and stop there.
But `HeadChk` is not an entry point. `PlayerBGCollision` has **exactly one caller** (5610, in
`PlayerCtrlRoutine`), and `ChkCollSize`/`HeadChk` are reachable only by falling through
`ChkOnScr` twenty lines earlier:

```
11919 ChkOnScr: lda Player_Y_HighPos
11920           cmp #$01
11921           bne ExPBGCol      ; <-- Mario must be on screen page 1
11922           lda #$ff
11923           sta Player_CollisionBits
11924           lda Player_Y_Position
11925           cmp #$cf
11926           bcc ChkCollSize   ; <-- and Y must be < $CF
11927 ExPBGCol: rts
```

So the whole routine runs only for **`Player_Y_HighPos` = 1 and `Player_Y_Position` ∈ [$00,
$CE]**. Every Y value F210 and F216 rely on ($DE–$FF, $EC–$FB, $FC–$FF, $FE–$FF) is ≥ $CF and
returns at 11927 before the head check exists. And "Mario above the top of the screen" is
`Player_Y_HighPos` = 0, which fails at 11921 — the two guards are independent and either one
alone is sufficient.

Enumerating the head row `((Y + adder) & $F0) − $20` over the *actual* reachable domain:

| configuration | extent (Y ≥) | `$eb` | head adder | Y range | head row |
|---|---:|---:|---:|---|---|
| big, upright | $20 | $00 | $04 | $20…$CE | $00…$B0 |
| big, swimming | $20 | $07 | $02 | $20…$CE | $00…$B0 |
| big, crouching | $10 | $0e | $12 | $10…$CE | $00…$C0 |
| small | $10 | $0e | $12 | $10…$CE | $00…$C0 |

(Small Mario can never crouch: `PlayerMovementSubs` (5875) forces `CrouchingFlag` = 0 whenever
`PlayerSize` ≠ 0, so `ldx PlayerSize / inx` never produces index 2 into the two-entry
`PlayerBGUpperExtent` either.)

**The head row is always $00…$C0 — in-bounds, every time.** `PlayerHeadCollision` (7219) latches
`$02`/`$06` *as left by that call*, so `Block_Orig_YPos` / `Block_BBuf_Low` can never hold a
wrapped address, and F207's deferred write through `BlockObjMT_Updater` has nothing OOB to write
to. The same closure applies to the other player paths:

- **feet** (`DoFootCheck`, adder $20): Y ≤ $CE ⇒ Y+$20 ≤ $EE, no carry ⇒ row ≤ $C0.
- **side, first half** (`SideCheckLoop`, `cmp #$20`, adders $08/$18): row $00…$C0.
- **side, second half** (`BHalf` 12050, `cmp #$08` — a *different, lower* bound than the first
  half, adder $18): $08 + $18 = $20 **exactly**. Row $00…$C0.

So **no player-driven block-buffer access in the game can leave the buffer.** Combined with
F215 (every writer's value set is {$00, $23, $c4, copy}) and F203 (the $06CF address ceiling),
the block-buffer OOB mechanism is now closed on **both** axes — geometry as well as value.

**What this changes.** open-threads #4 comes off Tier 2 entirely; Tier 3 #8's blocker is not
"exhibit a route position" but "there is no such position". H43 survives only on P3.1 §4's
genuinely unaudited classes (stack over/underflow, non-indexed writes, `VRAM_Buffer` overflow),
which is a much narrower and more honest statement of where ACE stands.

**The one writer that IS unguarded, and why it does not help.** `HandleEToBGCollision` (12436)
does `ldy $02 / lda #$00 / sta ($06),y` with **no `cpy #$d0` guard** — the only such store in the
ROM. Its geometry is reachable: `EnemyToBGCollisionDet`'s `SubtEnemyYPos` admits
`Enemy_Y_Position` ≥ 6, and `ChkUnderEnemy`'s `ldy #$15` gives adder $18, so **Y ∈ {6, 7}**
produces row $F0 — the wrap F210 was looking for, in the enemy path rather than the player one.
It needs an enemy of ID < $07 (or Spiny $12 / PowerUpObject $2E) at Y 6–7 standing on a `$23`
metatile (the temporary bouncing-block placeholder) on an odd page. The value is always `$00`,
which F215 already shows is inert as an `Enemy_ID`, so this is a **clearing** primitive only.
The one clear that is not inert is **`$06CC SecondaryHardMode`** (column 12), which gates
hard-mode-only enemies at parse time (`CheckEndofBuffer`, 7978): zeroing it mid-level suppresses
every hard-mode enemy not yet parsed — i.e. 8-3's Hammer Bros, the reason 8-3 is unmodelled.
Long shot, but it is the only live cell in the window and it is worth one line in the ledger.

**Two unbounded index loops the static audit cannot see** (`tools/oob_audit.py` classifies an
index by its last setter; these have no setter, they scan until a condition):
- `DuplicateEnemyObj` (8526): `ldy #$ff / FSLoop: iny / lda Enemy_Flag,y / bne FSLoop` — with all
  six slots occupied it walks past slot 5 into the zero page and **writes** `x|$80` at the first
  zero byte it finds ($0F+y), then `Enemy_PageLoc,y`, `Enemy_X_Position,y`, `Enemy_Y_HighPos,y`,
  `Enemy_Y_Position,y`. Called only where firebars or Bowser initialise — castle levels, i.e.
  **8-4**, the one unquantized level.
- `InitFireworks` (8634): `StarFChk: dey / lda Enemy_ID,y / cmp #StarFlagObject / bne StarFChk` —
  read-only, and the disassembly's own comment calls it an infinite-loop crash. It then sources
  the fireworks object's coordinates from whatever y it stopped at.

---

## 2. The framerule is one enemy slot's interval timer — and a second star flag deletes it

F27 already records *that* task 3 sets the star-flag object's `EnemyIntervalTimer` = 6 and task 4
waits on it. What has not been noticed is that **`RunStarFlagObj` is dispatched per enemy slot,
while the state it drives is global — except the one byte task 4 blocks on, which is per slot.**

`GameEngine` (5311) runs `ProcELoop` for x = 0…5; `EnemiesAndLoopsCore` → `RunEnemyObjectsCore`
→ `JmpEO` entry 29 for any slot whose `Enemy_ID` is `$31`. So with N slots holding $31:

- **Task 2 `AwardGameTimerPoints` (10487) runs N times per frame.** It subtracts one unit from
  the global `GameTimerDisplay` per *call*, so the countdown becomes ⌈T/N⌉ + 1 instead of T + 1.
- **Task 4 `DelayToAreaEnd` (10564) collapses.** Slot i finishes task 3, `DrawFlagSetTimer`
  writes `EnemyIntervalTimer[i] = 6` and bumps `StarFlagTaskControl` to 4. Slot j > i, processed
  later **in the same frame**, enters `DelayToAreaEnd` and reads `EnemyIntervalTimer[j]` — never
  written, therefore **0** — falls straight through to `IncrementSFTask2` → task 5.
  `PlayerEndLevel` sees 5 on the next frame and calls `NextArea`. **The (v+1)+105 wait — which
  *is* the framerule, F27 — becomes one frame.**

Priced on the WR (T and v from `tools/slack_table.py`):

| level | T | countdown now → N=2 | end wait now → N=2 | saved |
|---|---:|---:|---:|---:|
| 1-1 | 370 | 371 → 186 | 126 → 1 | 310 |
| 4-1 | 340 | 341 → 171 | 118 → 1 | 287 |
| 8-1 | 200 | 201 → 101 | 109 → 1 | 208 |
| 8-2 | 338 | 339 → 170 | 108 → 1 | 276 |
| 8-3 | 244 | 245 → 123 | 117 → 1 | 238 |
| | | | | **≈ 1,319** |

The second-order effect is larger than the first: with the wait gone the level is **unquantized**,
so every frame saved in it counts 1:1 — the same property that makes 8-4 the only level worth
attacking today would apply to all five flag levels. `docs/open-threads.md`'s budget table
("a level only pays if it saves its **whole** framerule deficit") stops being true.

### Why it does not happen today
`CastleObject` (3712) creates the star flag past one guard at 3739:
```
   lda CurrentPageLoc
   beq ExitCastle       ; "if we're at page 0, we do not need to do anything else"
```
and `tools/area_data.py` shows **4-1, 8-1, 8-2 and 8-3 each carry a second `CastleObject` at page
0 column 0** — the castle you start beside — every one suppressed by that `beq`. (1-1 has only
the end castle.) Star flags are exempt from the *right-side* offscreen erase (11045) but **not**
the left-side one (11032, unconditional), so a mid-level castle's flag would not survive to the
flagpole even without the guard. `DuplicateEnemyObj` does not copy `Enemy_ID`. The only other
writers of `Enemy_ID` are level data and the two frenzy cells (F206) — which §1 has just shown
cannot be written.

**So H50 is, today, gated on the same missing primitive as H43 — but it is a much bigger prize
than anything else that primitive unlocks, and unlike H43 it can be *priced* without it.**

### The measurement to do (cheap, and it needs no exploit)
`build/harness --poke` already exists (added for F251). Poke `Enemy_ID+k = $31` and
`Enemy_Flag+k = 1` for a spare slot k a few frames before 1-1's flagpole grab and read the next
area-load frame. One run confirms or kills both halves (countdown division and wait collapse).
This is the same 20-minute shape as F251's `--poke 0x6d6` test and it settles the highest-value
untested claim on the board.

---

## 3. `TimerControl` closes H3 — the arithmetic, and why every reachable freeze loses

H3 ("framerule-phase manipulation") is still open at Tier 4. `docs/timing-model.md` §10 leaves
"whether `TimerControl` freezes can shift the ITC phase relative to the level" unresolved. It can,
and it loses.

`DecTimers` (785): a non-zero `TimerControl` skips `IntervalTimerControl` **and every timer**,
but still increments `FrameCounter`, steps the LFSR and runs `OperModeExecutionTree`. That is a
genuine phase shift of the framerule grid *relative to the level*, which pause (F62) is not.

For a freeze of k frames of which c cost Mario progress, with v₀ the level's slack:

  **Δ = c + ((v₀ + k − c) mod 21) − v₀** ⇒ a gain needs **c + ((k−c) mod 21) < 21**.

Two structural notes: the freeze must fall **between the level's load and its T_set** (each flag
level re-anchors to the grid, so a shift applied earlier translates and cancels), and
`InitializeArea` clears $0747, so it is a per-level lever, not a cumulative one.

`TimerControl` is written from **exactly one site** — `SetPRout` (11419, `ldy #$ff`) — reached by
`ForceInjury`, death, size change and fire flower, and cleared by `DonePlayerTask` (5772) /
`ContinueGame` (2996). The only freeze during which Mario still moves is `PlayerInjuryBlink`
(5744): frozen while `TimerControl` ≥ $F0 (16 frames), **fully controllable** from $EF down to
$C9 (39 frames), ended at $C8. So k = 55, c = 16, d = 18, c + d = 34 → **Δ = +13 frames at best**,
and it costs a mushroom to be big first. `PlayerChangeSize` and `PlayerFireFlower` freeze Mario
for the whole window (c = k) ⇒ Δ = c.

→ H3 refuted for every freeze the ROM can produce. Kept only as a *price* for an arbitrary write
to $0747: a 1-frame freeze at c = 0 in a level with v₀ = 20 is worth 20 frames.

---

## 4. The non-gameplay budget, measured — for the strategy picture

`docs/open-threads.md` prices the movement surface at **290 frames** (F245). For comparison, from
the same dump:

| block | frames | % of 17,868 |
|---|---:|---:|
| `ScreenRoutines` (level-load screens) | 1,471 | 8.2 % |
| End-of-level (walk + countdown + raise + wait) | 2,787 | 15.6 % |
| Pipe timers (4 × 48 down, 2 × 160 intro side) | 512 | 2.9 % |
| **total non-gameplay** | **≈ 4,770** | **≈ 26.7 %** |

End-of-level breakdown: countdown 1,497 (F27's 1 frame per timer unit — 8.4 % of the movie in the
timer alone), grab→castle-door walk 552, flag raise 160, area-end wait 578.

**The intermission card, priced route-wide.** F28 gives the law (`control = load + 154 + w`); the
*cost* is what matters here. Measured `OperMode_Task` = 1 lengths: 149 / 161 / 162 / 161 / 157 /
161 / 161 / 161 for the eight card-showing loads (1-1, 1-2 intro, 4-1, 4-2 intro, 8-1, 8-2, 8-3,
8-4) against **22** for every sub-area load — i.e. **exactly 127 + w** per card, Σ = 8×127 + 81 =
**1,097 frames**. That is 52 framerules against a whole-route movement budget of 290 frames.

Both skip flags are structurally 0 at every one of those loads, and the argument is tighter than
"we never see it set":
- **`$0769 DisableIntermediate` has exactly one writer in the ROM** — `IntroEntr` (5514), on the
  last frame of the 1-2/4-2 intro pipe walk — and `SecondaryGameSetup` (2733) clears it at
  `OperMode_Task` 2 of *every* area load, i.e. after `ScreenRoutines`. It can only ever be
  non-zero for the one load that follows an intro area.
- **`$0752 AltEntranceControl`** is cleared at `PlayerRdy` (5547) two frames into every level, and
  each of its non-zero writes (5661 cloud, 5678 vine, 5710 pipe) is part of a transition that
  itself triggers the load. F251 already established that the warp branch forces mode 0; the
  reason it cannot be dodged is that `WarpZoneControl` cannot be *cleared* during the 48-frame
  descent either — its only writers are `ScrollLockObject_Warp` (3576, writes 4/5/6) and the
  self-erasing `inc` in `WarpZoneObject` (6483), plus the per-area-load clear.

This does not open a route. It puts a number on the E10/H43 write-reachability question:
**$0752 or $0769 = 1,097 frames; a second `Enemy_ID` = $31 = 1,319 frames and the framerule.**

---

## 5. Smaller findings, recorded so they are not re-derived

- **The game timer is a 1:1 cost and carry-over is not a lever.** `Entrance_GameTimerSetup`
  (2863) skips the reload when `FetchNewGameTimerFlag` ($0757) = 0 *or* the header's
  `GameTimerSetting` = 0 — but `NextArea` (5865) and `HandlePipeEntry` (12315) both set the flag,
  and after a flagpole the countdown has already driven the timer to **000**, so a carried timer
  across a flagpole is an instant `TimeUpOn` death (6469). Across the two warps it is 347 → 4-1
  (≈ −53 frames) and 356 → 8-1 (≈ **+56**): net ≈ 0. No stale `DigitModifier` can ride into the
  countdown either — `EraseDMods` zeroes $0134–$0139 at the end of every `DigitsMathRoutine` call.
  **Corollary worth carrying in every bound we quote:** a frame saved in a flag level is worth 1
  frame *except* when it crosses a 24-frame `GameTimerCtrlTimer` tick, where it is worth 0.
- **The side-pipe change-of-area timer is position-dependent** (`CheckSideMTiles`, 12085–12100):
  `AreaChangeTimerData` = **$A0 (160) when `ScreenLeft_PageLoc` = 0, $34 (52) otherwise**, and is
  **not written at all** when `Player_X_Position & $0F == 0`. The 1-2/4-2 intro pipes pay 160
  because the intro area never scrolls a full page — Mario's auto-walk is capped at
  `MaxRightXSpdData[3]` = $0C while `GameEngineSubroutine` = 7 (`GetXPhy`, 6172). 108 frames × 2
  sit behind a page boundary the level geometry cannot reach.
- **Row-13 area objects index up to 64 deep into a 47-entry jump table** (`DecodeAreaData`
  `Mask2MSB` → `RunAObj` `adc $07` with $07 = $22). Bounded only because the byte comes from ROM
  level data — so a **misaligned `AreaDataOffset` ($072C) would be immediate ACE**.
  `IncAreaObjOffset` only ever adds 2, so alignment holds today; flagged for any future glitch
  that touches the parser's offset.
- **`Enemy_ID` $34 is `WarpZoneObject`**, whose entire body is `inc WarpZoneControl` guarded by
  `ScrollLock` and a Y-parity test (6476) — consistent with F38 and with H49's chain.
- **`DisplayTimeUp` skips task 5** when `GameTimerExpiredFlag` is clear (`inc ScreenRoutineTask`
  *and* `IncSubtask`), so the card path is task 4 → 6 → 7. A time-up adds a *second* 7-tick wait.
- **Star flags are erased off the left but not off the right** (11032 vs 11045) — the asymmetry is
  what makes §2 hard.

---

## 6. What E10 has and has not covered

Covered this pass: the NMI/timer core, `OperModeExecutionTree` and all four mode trees,
`ScreenRoutines` end to end, the area parser and its jump tables, `GameRoutines`/`GameCoreRoutine`,
player physics and **all** of `PlayerBGCollision`, the block-object path, the enemy dispatch and
frenzy path, `RunStarFlagObj`, `RunGameTimer`/`DigitsMathRoutine`, the pipe/warp transitions, and
every `sta ($06),y` site with its guards.

Still unread, and still on E10's list: the sprite/OAM paths (`SpriteShuffler`,
`SprDataOffset`-indexed writes into `Sprite_Data`), the sound engine's RAM footprint
($07B0–$07CF), the `VRAM_Buffer` overflow class that P3.1 §4 explicitly left uncovered, the
two-player/demo/attract paths, and the remaining `JumpEngine` call sites outside the enemy and
area-object tables. The `VRAM_Buffer` class is the most interesting of those: it is the one
unaudited write class that H43 still rests on after §1.


---

## 7. Pass 2 — the zero-page write class, and the complete `Enemy_ID` writer census

**Why this class, and why it had never been read.** H50 needs `$31` in a spare `Enemy_ID` — and
`Enemy_ID` is **`$16`**, `Enemy_Flag` is **`$0f`**: both in the **zero page**. Every audit before
this aimed at page 6/7 targets ($06D6, $0750, $075F), and because zero-page indexed addressing
wraps inside the zero page, `tools/oob_audit.py` **excludes zero-page bases by construction**
(`docs/oob-audit.md` line 6). So the one class that can reach H50's target had been filtered out
of every previous pass.

`tools/oob_audit.py --target` now handles a zero-page target (index needed = `(target - base) mod
256`, since the wrap makes every zero-page base reach every zero-page address). Result for `$16`:
**320 stores can reach `Enemy_ID`** — 13 because their base *is* `Enemy_ID` (the normal in-range
writes), and **299 only with an index register ≥ 7**, which no index in the enemy code takes
(`ObjectOffset` ≤ 5, and every loop counter is bounded by its own `cpx`/`cpy`).

### The census that settles it
Rather than bound 299 index registers, enumerate the other side — **every store into `Enemy_ID`
in the ROM, and the value it writes**:

| line | value written | reachable? |
|---|---|---|
| 3762 `CastleObject` | **`#StarFlagObject` = $31** | the one and only $31 writer; guarded by `lda CurrentPageLoc / beq ExitCastle` and `FindEmptyEnemySlot` (x ≤ 5) |
| 7874 `ChkEnemyFrenzy` | **`EnemyFrenzyQueue` ($06CD)** | arbitrary byte — but only writable via the block-buffer mechanism, closed by F252/F253 |
| 8010 `StrFre` | **`EnemyFrenzyBuffer` ($06CB)** | same |
| 3873, 4158, 6679, 6805, 7995, 8301, 9176, 10289, 11485 | constants ($0d, $32, $2f, $33, $02, $11, $00, $2d, $fd) | — |
| 8705 `Set17ID` | `SwimCC_IDData,y` — a **2-entry** constant table | — |
| 8791 `HandleGroupEnemies` | `$01`, set by `sty $01` from Y ∈ {$00, $06, $02} | constants; index bounded by `cpx #$05` |
| 11152 | `BowserIdentities,y` (constant table) | — |
| 12465 `Demote` | `and #%00000001` → 0 or 1 | — |

**So the injector set is exactly {`CastleObject`, `$06CB`, `$06CD`} and nothing else.** Every
other path writes a compile-time constant. That is a much stronger statement than "we haven't
found one".

### The closest structural near-miss, and why it does not fire
`CopyFToR` (10275–10289, Bowser's rear) is the only place in the game where zero-page object
arrays are indexed by a **RAM cell** rather than by a slot counter — `DuplicateObj_Offset`
($06CF), which is **exactly F203's proven OOB write ceiling**, i.e. the one index byte in the
game that the block-buffer mechanism can reach at all. It does:

```
CopyFToR: … ldy DuplicateObj_Offset
          sta Enemy_X_Position,y      ; $87+y  <- Bowser's X ± $10   (a CONTROLLABLE value)
          sta Enemy_Y_Position,y      ; $cf+y  <- Bowser's Y
          sta Enemy_State,y / sta Enemy_MovingDir,y
          ldx DuplicateObj_Offset
          lda #Bowser / sta Enemy_ID,x
```
Reaching `Enemy_ID+0` through the value-carrying write needs `y = ($16-$87) mod 256 = 143`, and
the `sta Enemy_ID,x` writes the constant `$2d`, not `$31`. Three independent reasons it is dead:
(a) the only value the surviving block-buffer writer can place in $06CF is **`$00`** (F253);
(b) `DuplicateObj_Offset`'s own writer is `DuplicateEnemyObj`'s `FSLoop`, which stops at the first
zero `Enemy_Flag,y` from $0f up — `$15` (a seventh flag byte) is **never written by any other code
in the ROM**, so the scan halts at y ≤ 6; (c) it is Bowser/firebar code, i.e. castle levels only —
8-4, which has no flagpole.

Worth recording as a mechanism even so: **`DuplicateEnemyObj` is a monotonically advancing
zero-page write walker.** Each call writes `x|$80` into the zero byte it lands on, so the *next*
call necessarily lands further up. Its budget is the number of firebar/Bowser inits in the level,
and its collateral writes ($6e+y, $87+y, $b6+y, $cf+y) scribble player state as y grows.

### Verdict for pass 2
**The zero-page class is closed.** It contains no new injector: the only writer of `$31` is
`CastleObject` (page-0 guarded, once per non-page-0 castle, and no route level has two), and the
only variable-valued writers of `Enemy_ID` are the two frenzy cells. So H50's remaining question
is not "what can write `Enemy_ID`" — it is unchanged and now provably singular:

> **Can anything write a non-zero byte into `$06CB` or `$06CD`?**

and the block-buffer mechanism (the only candidate anyone had) is closed on both axes by F252 and
F215. What is left is the two write classes still unread: **stack over/underflow** and
**`VRAM_Buffer` overflow** (writes indexed by `VRAM_Buffer1_Offset`, advanced +7 by
`GetPlayerColors`, +10 by `WriteBlockMetatile` and +3 by `OutputNumbers`, with only
`ColorRotation` bounding itself at `cpx #$31`). That is pass 3.


---

## 8. Pass 3 — the last two write classes, and the complete writer set of the frenzy cells

Pass 2 reduced H50 (and with it H43) to one question: **can anything write a non-zero byte into
`$06CB` or `$06CD`?** This pass answers it by enumeration rather than by search.

### 8.1 The two "unaudited classes" cannot reach page 6 at all

- **`VRAM_Buffer` overflow.** Every indexed store into the buffers is `VRAM_Buffer1+d,x/y` or
  `VRAM_Buffer2+d,x/y`; the largest displacement in the ROM is **+27**
  (`sta VRAM_Buffer1+27,y`, `PrintWarpZoneNumbers`). With an 8-bit index the maximum effective
  address is `$0301 + 27 + 255 = $041B` for buffer 1 and `$0341 + 4 + 255 = $0444` for buffer 2.
  **Page 4 is the ceiling** — 647 bytes short of `$06CB`. However far
  `VRAM_Buffer1_Offset` runs, this class cannot touch the frenzy cells. (It *can* corrupt
  `$0400`–`$0444` = `SprObject_X_MoveForce` / `Enemy_X_MoveForce` / `YPlatformTopYPos`, which is
  worth remembering for other purposes, but not for this one.)
- **Stack over/underflow.** `pha`/`php`/`jsr` write `$0100 + S` with an 8-bit S that wraps inside
  page 1. **Page 1 is the ceiling.** Same conclusion.

So the two classes P3.1 §4 left uncovered — the two things H43 was still resting on after F252 —
are both structurally incapable of reaching the target.

### 8.2 The complete writer set of `$06CB` / `$06CD`

**Indexed stores that can reach `$06CB`** (`tools/oob_audit.py --target '$06cb'`, 30 rows):
- `MetatileBuffer,x/y` (`$06A1`/`$06A2`) — needs index **42**, but every renderer loop is bounded
  by `cpy #$0b` / `cpx #$0d` / `cpx #$0b` (11 or 13). Residual noted below.
- `HammerEnemyOffset,y` (`$06AE`) — needs **29**; hammer slot counter.
- `Misc_Collision_Flag,x` (`$06BE`) — needs **13**; `ldx ObjectOffset` ≤ 5.
- the `(zp),y` block-buffer family — closed by F252 (no reachable geometry) and F253 (the one
  unguarded writer stores `$00`).

**Absolute stores** — all 13, with the value each writes:

| value | sites |
|---|---|
| `#$00` | 3615, 7879, 8613, 8862, 9977, 10153, 10454; 10147 (`KillAllEnemies`, A = 0 from `EraseEnemyObject`); 11147 (`HurtBowser`, A = 0 from `InitVStf`) |
| `#Spiny` = `$12` | 9981 |
| `#BowserFlame` = `$15` | 10260 |
| `#Fireworks` = `$16` | 10528 |
| `Enemy_ID,x` | 8832 (`InitEnemyFrenzy`) — **but** it is dispatched from `InitEnemyRoutines[Enemy_ID]`, whose `InitEnemyFrenzy` entries are only `$12`, `$14`, `$15`, `$16`, `$17`. It copies one of those to itself. `$31` maps to `NoInitCode`, so the star flag never passes through it. |
| `FrenzyIDData-8,x` = `$14`/`$17`/`$18` | `ExitAFrenzy` (3615's path), x fixed at 8/9/10 by the jump-table entry that reached it |

**So the writable value set is `$06CB` ∈ {$00, $12, $14, $15, $16, $17} and
`$06CD` ∈ {$00, $14, $17, $18}.** `$31` is in neither, and neither is any out-of-table value.

### 8.3 What that closes

**H50 is unreachable.** The mechanism is measured and real (857 frames at N = 2, 1,329 with the
music, F258/F259), the injector set is exactly {`CastleObject`, `$06CB`, `$06CD`} (F261),
`CastleObject` fires once per non-page-0 castle and **no area in the game has two** (§8.4), and
the two frenzy cells cannot be given a non-zero value they were not designed to hold.

**H43 / the ACE line closes with it, and by the same enumeration.** F207/F208 confirmed the
out-of-table jump *fires* when `$06CB` is poked to `$c4`. But `$c4` is not in the writable set —
and neither is anything else `≥ $37`. **The arbitrary jump exists and can never be armed.**

### 8.4 The castle question, answered across all 34 areas

Raised by the user: if `CastleObject` is the only `$31` writer, can we get past its guard? The
guard (`lda CurrentPageLoc / beq ExitCastle`) is not the obstacle — it only suppresses the *page-0*
castles. The obstacle is the level data. Decoding **every** area with `tools/area_data.py`:

- every ground area is either `[page-0 castle, end castle]` or `[end castle]` alone
  (1-1 = `L_GroundArea6` is the only one with just the end castle);
- **no area in the game has two castles at a non-zero page**;
- the only mechanism that re-parses level data is `ExecGameLoopback`, driven by `LoopCmd` objects,
  and those exist **only** in `L_CastleArea2` / `L_CastleArea5` / `L_CastleArea6` (4-4, 7-4, 8-4)
  — which contain no `CastleObject` at all and have no flagpole.

Also checked and dead: entering a level at a non-zero `HalfwayPage`/`EntrancePage` makes
`CurrentPageLoc` non-zero at load, but the page-0 castle is then *behind* the renderer and
`ProcessAreaData`'s `CheckRear` (`AreaObjectPageLoc < CurrentPageLoc → SetBehind`) skips it
without decoding.

### 8.5 Residuals — what this does NOT prove

1. **The `MetatileBuffer` renderer loops are bounded by their start row, not by an explicit test.**
   `ChkCFloor: cpx #$0b / bne CRendLoop` increments x, so a start row above `$0b` wraps the whole
   way round — 255 iterations writing `MetatileBuffer,x` across pages 6 and 7. The disassembly
   comments this at `CastleObject`: *"if starting row is above $0a, game will crash!!!"*. The start
   row comes from `GetLrgObjAttrib` on ROM level data, and no level triggers it (the game does not
   crash), but I have verified that by inference from the game's behaviour rather than by decoding
   every object's sub-row. Even if one did, the values written are `CastleMetatiles` ($45–$4b, $00)
   and terrain metatiles — still not `$31`.
2. **A misaligned `AreaDataOffset`** would make `RunAObj` dispatch out of its 47-entry table (§6),
   which is arbitrary code and could write anything. Nothing in the ROM misaligns it
   (`IncAreaObjOffset` only ever adds 2), but that is the one door that would reopen everything.
3. Emulator-level or power-on state outside the game's own model (H20) is not addressed here;
   `$06CB` is cleared by `InitializeMemory` at every area load.
