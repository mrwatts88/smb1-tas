# Open threads — everything left, and what "give up" would mean

**Rewritten 2026-08-25 (session 20, after E10 closed the state surface).** Regenerate the
hypothesis half with `grep '^| H' docs/hypotheses.md`. The previous version tiered 21 items by
"running / ready / blocked / long shot"; that shape stopped fitting once a whole tier closed in a
day, so this version leads with **the live board** and files everything closed at the bottom with
its date and fact number.

---

## THE LIVE BOARD — six items, and that is all of it

| # | thread | needs | has | state |
|---|---|---|---|---|
| **L1** | **8-2's flag-glitch window** (H48/F247) — the jump over the col-206/207 wall reaches the pole 112 frames early but takes a normal slide instead of HappyLee's glitch. A ~4 px band in `Player_Y_Position` (161 reached, 165–166 needed) at the frame `x+13` crosses into column 216. | 19 | 112 | **RUNNING**, Mac ×2 (`runs/E9b/arc{16,32}.log`, 6 h). At the control (`best=12953` vs baseline 12952), no banked frames yet |
| **L2** | **1-2's eight frames** (H22 / H46-dynamic) — the clip's *entry* costs the speed (F246); the traversal is free. A sink entry that keeps the speed (F244) is priced at ~13 frames of overshoot against a deficit of 8. | 8 | 60 | **RUNNING**, Linux ×3 (`runs/E7-w12/{body,sub16,sub32}.log`). At the control (`best=3764` vs baseline 3763), no banked frames yet |
| **L3** | **8-4 room 3's approach** (H25) — one frame, in the only unquantized level. Two searches went dry but **both goaled on the WR's own apex**, which H39's seam corollary says deletes the answer by construction. The corrected version searches the 162-frame approach with generic buckets and emits a *set* of apex states. | 1 | 38 | **un-run** |
| **L4** | **8-4 room 2's exit pipe** — 15 frames of measured geometric loss at cols 150–152 (F245): an approach *arc* onto the pipe mouth (speed 38→23 against the c152/c153 block stack), never searched with a subpixel cell key. MrWint's 40-frame segment optimum does **not** cover it — it fixes the state at x 2373, which is exactly what the approach chooses (H39's seam corollary). Goal = the record quantity with the monotonicity argument written down, and the wrong-pipe trap observed in the control (F267). (Its sibling, 4-2's warp-zone drop, is 30 frames but 4-2 needs 13 and is measured closed on both routes.) | 1 | 15 | **RUNNING**, Linux — root `a` at 40,000 cells (`runs/L4-w84r2/a.log`, `docs/experiments/L4-w84r2-pipe.md`); control green at `GOAL frame=16182 +0`. Root `w` (whole room) written, RAM-blocked |
| ~~L5~~ | **CLOSED 2026-08-25 (F264) — H2, lag frames.** The overrunning routine is `InitializeArea`/`InitializeMemory`, not `InitScreen`: a 1,868-byte RAM clear at 18 cycles/byte = ~33,370 cycles + ~2,000 prologue against an NTSC frame's 29,780 = **119 %**, so exactly one NMI is lost per load and never two. Overrun ~5,600 cycles; the only parameter can save 1,368. Irreducible, and nothing about it is ours. (Route has **17** load lag frames, five inside 8-4.) | 1 | **0** | **closed** |
| **L7** | **The novelty sweep on 8-4 — the one unquantized level — with the object-slot lens it never had.** Two gaps, both now addressed. (a) `build/explore --anomaly` (`runs/E6-vram/`) was run on 1-1, 1-2, 4-1, 4-2, 8-2 and 8-3; **8-4 was never swept, in any of its five sub-areas** — the level where one frame *is* the record had had no corner-search at all. (b) **No sweep ever carried an object-slot lens**, and F266 shows why that mattered: the nearest class fired only on `Enemy_ID > $36` over five of the six slots, so `$31` (`StarFlagObject`, the class F258 priced at 857 frames) was invisible to it in every slot. explore.c now has class 17 (`Enemy_ID` novel in a **live** slot, calibrated) and class 18 (a **second** star flag, calibrated by count), and class 5 covers all six slots. Roots = the five sub-area control frames (F265). Note what this is *not* competing with: L1/L2's running archives are goal-directed optimizers over the joypad and by construction cannot surface a structural anomaly (all of session 19's real finds came from reading, not from 809 M simulated frames). | 1 | ? | **RUNNING**, Linux — `r5` (Bowser room) live, `r1`–`r4` queued behind the E7 archives (`runs/L7-w84/`, `docs/experiments/L7-w84-sweep.md`). Follow-up: re-run E6's six roots with the object lens |
| **L6** | **Big Mario, route-wide** (H18/F238) — his left probe covers two rows, so he free-passes a face more easily, but he is strictly fatter and the static census says he adds nothing (F243). | — | — | fold into L2; **not its own campaign** |

**Where the frames can actually come from.** A level only pays if it saves its **whole** framerule
deficit — except 8-4, which is unquantized and pays per frame. From `tools/slack_table.py` and the
loss map (F245):

| level | must save | movement loss available | note |
|---|---|---|---|
| **8-4** | **any 1 frame** | 38 (room 3) + 15 (room 2 pipe) | **the only 1:1 level — L3 and L4 both live here.** Its 5 lag frames are NOT available (F264) |
| 8-2 | 19 | **114** | L1 running |
| 1-2 | 8 | 60 | L2 running |
| 4-2 | 13 | 33 + 30 | measured closed on both routes (F122/F123) |
| 4-1 / 8-1 / 8-3 | 9 / 18 / 10 | **0** | geometry cannot pay here |
| 1-1 | 1 | 0 | proven closed end to end (F124) |

**The whole route loses 290 frames to geometry (F245)** — that is the entire budget the movement
side is fighting over. **8-4 is the thread**: it is the only level where one frame *is* the record,
and three of the four un-run items sit in it.

> **Caveat that would rewrite this table (F258/F259):** H50 — a second star-flag object — removes
> the end-of-level wait and makes every flag level unquantized like 8-4, collapsing the "must save"
> column to 1 and reviving every banked sub-threshold frame. It is **measured at 857 frames**
> (1,329 with the win music dropped) and **unreachable** (F262). Price movement work against the
> "must save" column as it stands, but know the other column exists.

---

## Structural long shots — low prior each; any one reopens everything

Kept because you cannot prove a negative about mechanisms nobody has enumerated. None is a session's
work on its own; each is a lens to apply while doing something else.

- **H47 — an over-cap forward displacement mechanism.** *This is the unstated premise behind every
  closure on the board.* Every x bound prices per-frame progress at the running cap (40 subpixels).
  A collision-push chain, platform carry, enemy interaction or coordinate wrap that beats it would
  invalidate F124, F225, F122/F123, F232 and F152 **simultaneously**. Prior low (F227, F120, F231
  each looked and found nothing), but state the premise so that if a mechanism ever turns up it is
  immediately obvious what it invalidates. **PRICED 2026-08-25 (F270): the class is worth up to
  127 px ≈ 50 frames.** The furthest right the game permits is `ScreenRight_X_Pos − 16`, and the WR
  runs a median 127 px behind it in every level measured. **And one such mechanism now exists**
  (F268) — it is just clamped away (F269) or needs a vine (F270). The prior is no longer "nothing
  has ever turned up".
- **H31** — a crack in an unmodeled mechanic rather than in player movement (platform/lift carry,
  enemy interactions, scroll coupling). Every solved segment has the WR on the *player-only* bound.
- **H32** — the 4-2 lift as a launch pad (jump from the descending lift at Y 132, not the floor at 176).
- **H12** — L+R / U+D semantics beyond the known 1-frame reversal. **PARTLY ANSWERED 2026-08-25
  (F268/F269/F270, `docs/experiments/H12-input-semantics.md`): an effect exists.** `PlayerFacingDir`
  = 3 (L+R) and = 0 (L+R on a vine) are out-of-range indices into `PutPlayerOnVine`'s two 2-byte
  adder tables; facing 3 teleports Mario **+24 pages (x 3063 → 9471, measured)** and facing 0 moves
  him **+131 px in-page with no clamp**. It does not pay on this route — the page-scale form is
  clamped back (F269) and the in-page form needs a vine, which 8-4 lacks. Still unread: the other
  facing/moving-dir readers. **Swimming is now CLOSED (F271):** water runs four caps (40/24/16/12);
  the swim cap is **24** and the game's own 40 cap unlocks at `Player_XSpeedAbsolute >= 25` — **one
  unit short** — worth **259 frames** in 8-4's water room. Measured open by poke, proven unreachable
  by enumerating all eight writers of `Player_X_Speed`. **Standing note: anything that ever adds 1 to
  `Player_X_Speed` in a water area is worth 259 frames**, because the state self-sustains above the
  threshold.
- **H16** — sprite-0 / PPU timing: prevent a lag frame by controlling what renders. *(Overlaps L5.)*
- **H17** — object-slot spawn suppression: suppress Bowser in 8-4 for a faster axe. *(L7's `r5` root
  sits in that room and carries the new object-slot lens, so it is being looked at in passing.)*
- **H20** — uninitialised-RAM reads under the emulator's defined initial RAM.
- **H14** — vine teleport **refuted** (F268/F269: real, +6,406 px, clamped back, −111 px net; and
  8-4 has no vine). *Screen-edge* tricks are not: F270 measures **127 px of legal headroom** to the
  right of where the WR runs.
- **H4** — time-bonus countdown phase at the flagpole. *(F257 gives the arithmetic: a frame saved in
  a flag level is worth 1 except when it crosses a 24-frame tick, where it is worth 0.)*
- **H1** — ending-input coast: a final jump from farther away that makes the *last input* earlier
  while Mario still reaches the axe. Partly closed (F223 settled the WR's own final jump). *(L7's
  `r5` job is the only sweep whose horizon reaches the ending, so its `best_*.path` — anything with
  `last_input < 17846` — is a live H1 probe as a side effect.)*

---

## Closed — with the date and the artifact, so nobody re-opens them by accident

**2026-08-25 (session 20, E10 — the ROM read end to end, `docs/experiments/E10-rom-read.md`):**

- **H43(b) — the head bump at `Y + adder < $20`** — *was* "the single highest-leverage missing
  primitive in the project". **Refuted (F252):** `PlayerBGCollision` is entered only past `ChkOnScr`,
  which requires `Player_Y_HighPos` = 1 **and** `Player_Y_Position` < $CF; every Y window F210/F216
  derived is >= $CF. No player-driven block-buffer access can leave the buffer. **F210 and F216 are
  corrected.**
- **The three unaudited write classes** — zero-page (F261), `VRAM_Buffer` overflow and stack (F262).
  `VRAM_Buffer` tops out at `$0444`, the stack at `$01FF`; neither reaches page 6.
- **H7 / H8 / H43 — cart-swap-free ACE (F262).** The out-of-table jump *fires* (F207/F208) but
  `$06CB` in {$00,$12,$14,$15,$16,$17} and `$06CD` in {$00,$14,$17,$18} — **it can never be armed.**
- **H49's residual (F262)** — needed `$06D6` and `$0769`, both above every ceiling; same enumeration.
- **H50 — the second star flag (F258/F259/F262).** Mechanism measured at **857 frames** (1,329 with
  the music); injector does not exist and cannot be made to exist. `CastleObject` is the only `$31`
  writer in the ROM and **no area in the game has two non-page-0 castles** (F263).
- **H3 — framerule-phase manipulation (F255).** `TimerControl` really does shift the ITC grid, but
  every freeze the ROM can produce loses (injury: k=55, c=16 -> +13 frames at best).

**Earlier:** H46's static half (F243, the wall-face census is empty at both hitboxes); H48 confirmed
as movement and refuted as a record (F247); 1-1 (F124); 4-2 both routes (F122/F123); 4-1/8-1/8-3
(F225).

**Retired in practice** (open in the ledger, not worth a session): **H10/H11/H23** restate "search
harder" and are superseded by the priced loss map; **H41/H42** are search-methodology, useful only
inside another unit; **H15** (soft reset), **H26** (8-2 Koopa FPG), **H19** (Start-press alignment,
settled for this boot by F31).

---

## What "give up" would actually mean

The old condition was *"Tier 1 dry, Tier 2 done, and E10 clean."* **E10 is now clean** and the state
surface is closed. So the remaining condition is narrow and concrete:

> **L1 and L2 dry, L3/L4 run and dry, and L7 — the novelty sweep — run to completion on 8-4.**
> (L5 closed 2026-08-25, F264.)
>
> **L7 is explicitly part of the condition (user, 2026-08-25).** It is the only *structural* look at
> the only unquantized level; L1-L4 are goal-directed optimizers over the joypad and by construction
> cannot surface an anomaly. Do not treat the sweep as optional colour — a dry board without it is
> not a dry board.

That is one to two sessions of work, not three to four. If it lands there, PLAN §7 already treats
"the census is empty and the audit is clean" as a tier-1 publishable result in its own right rather
than a failure — a complete, measured account of why 17,868 is optimal on this route, plus two
measured mechanisms nobody had documented (H50's 857 frames; the 26.7 % non-gameplay budget, F256).

**The asymmetry has flipped.** The old note here said the movement surface was nearly licked clean
while the state surface "had barely been read, and every page of it read this session produced
something." That is no longer true: the state surface was read end to end on 2026-08-25 and is now
the *more* closed of the two. What is left is movement, in 8-4, worth one frame.
