# Open threads — everything left, and what "give up" would mean

**Written 2026-08-25 (session 19).** Regenerate the hypothesis half with:
`grep '^| H' docs/hypotheses.md`. Ledger state: **49 hypotheses, 22 closed with a proof artifact,
27 nominally open — of which about eight are real work and the rest are bookkeeping.**

## The frame budget, so every item below can be priced

A level only pays if it saves its **whole** framerule deficit — except 8-4, which is unquantized and
pays per frame. From `tools/slack_table.py`:

| level | must save | movement loss available (F245) | note |
|---|---|---|---|
| **8-4** | **any 1 frame** | 38 (room 3) + 15 (room 2 pipe) | the only 1:1 level |
| 1-2 | 8 | 33 (the clip) + 27 (the turnaround) | 3 searches running |
| 4-1 | 9 | **0** | geometry cannot pay here |
| 8-3 | 10 | **0** | geometry cannot pay here |
| 4-2 | 13 | 33 (bought — it mints the warp key) + 30 (warp zone) | both routes measured closed |
| 8-1 | 18 | **0** | geometry cannot pay here |
| 8-2 | 19 | **114** | 2 searches running |
| 1-1 | 1 | 0 | proven closed end to end (F124) |

**The whole route loses 290 frames to geometry (F245).** That is the entire budget the movement side
is fighting over, and more than a third of it is at one place in 8-2.

---

## Tier 1 — running right now

| # | thread | worth | state |
|---|---|---|---|
| 1 | **H48 — 8-2's flag-glitch window.** The jump over the col-206/207 wall is confirmed on the core (F247): clears at speed 40, reaches the pole **112 frames early**. It ends the level *later* because it takes a normal slide instead of HappyLee's glitch. The whole thing is a **~4 px band in `Player_Y_Position`** (161 reached, 165-166 needed) at the frame `x+13` crosses into column 216. | 19 needed, 112 in hand | 2 archives on the Mac (`runs/E9b/launch_mac.sh`), 21k fps, both at the control |
| 2 | **H22 / H46-dynamic — 1-2's eight frames.** The clip's *entry* costs the speed (F246: 40 → 0 → re-accelerate over 14 frames of +1 px drift); the *traversal* is free at full speed. If a sink entry exists that keeps the speed (F244), F239 prices it at ~13 frames of overshoot against a deficit of 8. | 8 needed | 3 archives here (`runs/E7-w12/`), all at the control |

---

## Tier 2 — concrete, ready to start, no missing primitive

3. **E10 — the unaudited half of the ROM.** Pure reading, no compute. Never done: every `JumpEngine`
   call site's index provenance beyond the enemy tables (18 sites listed, only the enemy ones
   chased), every writer of the `$0780-$07A3` timers, the sprite/OAM paths, the sound engine's RAM
   footprint, and the two-player / demo / attract-mode paths. **Today gave it three named targets
   instead of a fishing licence:** `$0769` (`DisableIntermediate` — worth ~96 frames at 8-4's
   water-room transition, F251), `$074e` (`AreaType` — worth ~96 × 3 if writable before a pipe
   commit), `$06D6` (`WarpZoneControl`). *Best expected value per hour on the board.*
4. **H43(b) — a head bump at `Y + adder < $20` on an odd-page column 11.** This is the single
   highest-leverage missing primitive in the project. F250 showed `$06CB` is **inside** F203's
   proven `$06CF` OOB ceiling, and `$06CB` feeds `Enemy_ID` unchecked — so this one bump unlocks
   `WarpZoneObject`, arbitrary enemy IDs, and the whole H7/H8/H43 chain. It is a geometry question,
   which is what the search engine is for. **REFUTED 2026-08-25 by E10 (F252): there is no such Y.**
   `PlayerBGCollision` is entered only past `ChkOnScr` (11919-11926), which requires
   `Player_Y_HighPos` = 1 **and** `Player_Y_Position` < $CF — and every Y window F210/F216 derived
   is >= $CF. The reachable head row is $00-$C0 for every size/crouch/swim combination, and the
   feet and both side probes close the same way, so **no player-driven block-buffer access can
   leave the buffer.** With F203 (address ceiling) and F215 (values) the block-buffer mechanism is
   closed on both axes; F210 and F216 are corrected. What is left of H43 is #4' below.
4'. **E10 continued — the write classes nobody has read.** E10's first pass (2026-08-25,
   `docs/experiments/E10-rom-read.md`) covered the NMI/timer core, all four mode trees,
   `ScreenRoutines`, the area parser, player physics and **all** of `PlayerBGCollision`, the block
   and enemy dispatch paths, `RunStarFlagObj`, `RunGameTimer`, and every `sta ($06),y` site with
   its guards — producing F252-F257. Still unread and now load-bearing for #8: the **`VRAM_Buffer`
   overflow class** (writes indexed by `VRAM_Buffer1_Offset`, advanced +7/+10/+3 by
   `ColorRotation`, `GetPlayerColors`, `WriteBlockMetatile` and `OutputNumbers` — only
   `ColorRotation` bounds itself), the sprite/OAM paths, the sound engine's RAM footprint, the
   two-player/demo paths, and the `JumpEngine` sites outside the enemy and area-object tables.
   Same shape: pure reading, no compute.

4''. **H50 — a second `Enemy_ID` = $31 deletes the framerule (F254).** `RunStarFlagObj` runs once
   per frame *per enemy slot* holding $31, and its task 4 blocks on a **per-slot**
   `EnemyIntervalTimer` — so a second star-flag object reads its own untouched 0 and ends the area
   in one frame instead of (v+1)+105, while task 2 divides the timer countdown. Priced at N=2:
   **~1,319 frames, and all five flag levels become unquantized like 8-4** — which would rewrite
   the budget table at the top of this file. Reachability is blocked with #8, **but the prize can
   be measured today** with `build/harness --poke` (`Enemy_ID+k = $31`, `Enemy_Flag+k = 1` a few
   frames before 1-1's grab), the same ~20-minute shape as F251's test. **Cheapest high-value
   measurement on the board — do it before anything else in Tier 2.**

5. **H25 — 8-4 room 3's approach.** One frame, in the unquantized level. Two searches already went
   dry (F133) but **both goaled on the WR's own apex**, which H39's seam corollary says deletes the
   answer by construction. The un-run version searches the 162-frame approach with generic buckets
   and emits a *set* of apex states.
6. **Big Mario, route-wide (H18 / F238).** He is on screen for 4 of 18,268 frames in the WR. E9a
   showed his left probe covers **two rows** instead of one, so he free-passes a face more easily —
   but he is strictly fatter and the static census says he adds nothing (F243). Cheap to fold into
   the 1-2 work; do not run as its own campaign.
7. **The two unexplained loss sites.** 4-2's warp-zone drop (30 frames, cols 57-59) and 8-4 room 2's
   exit pipe (15 frames, cols 150-152). Both are arc problems, neither has been searched with a
   subpixel cell key.

---

## Tier 3 — real, but blocked on a primitive we do not have

8. **H7 / H8 / H43 — cart-swap-free ACE.** The arbitrary jump is *confirmed firing* (F207/F208/F209):
   `$06CB` reaches `Enemy_ID`, out-of-table indices dispatch, the destination is a deterministic
   function of the byte, and it reaches area-loading code. No value found yet ends the game early.
   ~~Blocked on #4.~~ **Its writer is now gone (F252/F253): the block-buffer mechanism cannot reach
   the window with a non-zero byte at all.** The whole ACE line therefore rests on the three write
   classes P3.1 §4 never audited — stack over/underflow, non-indexed writes, and `VRAM_Buffer`
   overflow. That is #4'.
9. **H49's residual (F251).** 8-4's water-room transition is the one whose *destination* is not a
   castle, so `DisplayIntermediate` there does consult `DisableIntermediate`: `$06D6` **and** `$0769`
   non-zero during that one descent is ~96 frames. Both bytes are above the proven ceiling → E10.
10. **H2 — lag frames.** 16 on the route, exactly one per area load (F224), four of them inside 8-4
    where a frame is a frame. Never attacked. Honest prior: the lag *is* the load, so probably
    irreducible — but it has never been read at code level, and that is cheap.

---

## Tier 4 — structural long shots. Low prior each; any one of them reopens everything

11. **H47 — an over-cap forward displacement mechanism.** *This is the unstated premise behind every
    closure in the project.* Every bound assumes 2.5 px/frame. A collision-push chain, a platform
    carry, an enemy interaction or a coordinate wrap that beats it would invalidate the entire
    movement-side case for optimality. Never systematically hunted.
12. **H31 — a crack in an unmodeled mechanic** rather than in player movement: platform/lift carry,
    enemy interactions, scroll coupling. Every solved segment has the WR sitting on the *player-only*
    bound, so a new frame most plausibly comes from something the model omits.
13. **H32 — the 4-2 lift as a launch pad** (jump from the descending lift at Y 132 instead of the
    floor at Y 176).
14. **H12 — L+R / U+D semantics** beyond the known 1-frame reversal.
15. **H16 — sprite-0 / PPU timing**: prevent a lag frame by controlling what renders.
16. **H20 — uninitialized-RAM reads** under the emulator's defined initial RAM.
17. **H17 — object-slot spawn suppression** (suppress Bowser in 8-4 for a faster axe).
18. **H14 — vine teleport / screen-edge tricks** skipping a section of 8-4 or 4-2.
19. **H3 — framerule-phase manipulation** (re-align a level with slack k).
20. **H4 — time-bonus countdown phase** at the flagpole.
21. **H1 — ending-input coast**: a final jump from farther away that makes the *last input* earlier
    while Mario still reaches the axe. Partly closed (F223 settled the WR's final jump).

---

## Retired in practice (open in the ledger, not worth a session)

**H10 / H11 / H23** are restatements of "search harder" and are superseded by the priced loss map.
**H41 / H42** are search-methodology hypotheses, useful only inside another unit. **H15** (soft
reset), **H26** (8-2 Koopa FPG), **H19** (Start-press alignment, settled for this boot by F31).

---

## What "give up" would actually mean

A defensible stop is: **Tier 1 dry, Tier 2 done, and E10 clean.** That is roughly three to four more
sessions. Tier 4 would remain open forever in principle — you cannot prove a negative about
mechanisms nobody has enumerated — but PLAN §7 already treats "the census is empty and the audit is
clean" as a tier-1 publishable result in its own right, not a failure.

The honest asymmetry to hold onto: the *movement* surface is nearly licked clean and we can now put a
number on it (290 frames, mostly measured shut). The *state* surface — write primitives, entrance
modes, area loads, the frenzy buffer — has barely been read, and every page of it read this session
produced something (F241-F251).
