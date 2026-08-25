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
