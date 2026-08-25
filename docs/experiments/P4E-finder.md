# Track E — the finder

Opened 2026-08-25 (session 18) under `docs/strategy-review.md`, which is the official plan.
Doctrine for this track: **find, don't prove.** Beams, sampling, restarts and archives are all
legitimate; only a *positive* gets verified (core replay, then two emulators).

---

## E1 — is level-entry state a pure function of the entry frame?

**Why it matters.** If yes, the game decomposes exactly into seven framerule lotteries plus 8-4,
per-level greedy is right, and H9/P2.4 close. If no, the framerule levels' slack (3–20 frames each,
free) is a zero-cost knob on 8-4's Bowser and cheep RNG — and 8-4 is the unquantized level.

**Method.** `tools/entry_state_scan.py` over `data/wr/fceux_wr.ram` (18,268 rows × 2 KiB):
per-frame deltas on `RandomBits` ($07a7–$07ae), `IntervalTimerControl` ($077f) and `FrameCounter`
($0009), plus a dump of every non-zero cell in $074c–$07ff three rows after each `AreaPointer`
change (`InitializeArea` clears $0000–$074b, so anything carried is above that).

**Result — E1 answers YES, with one structural rider (F224).**

| quantity | stalls | where |
|---|---|---|
| `RandomBits` | **22** | 1, 2, 3, 7, 8, 44, 614, 928, 1946, 2445, 3816, 6044, 6543, 7222, 7773, 10815, 12958, 15059, 15797, 16234, 16599, 17469 |
| `IntervalTimerControl` | 23 | the same list plus row 5 |
| `FrameCounter` | 6 | 1, 2, 3, 4, 5, 8 — boot only |

The `RandomBits` stall set is **exactly the boot frames plus one frame per area load** — it is F30's
24 lag frames seen from the RNG side, and each stall row is `load_row − 1` (8-4's four sub-area
loads at dump 15798/16235/16600/17470 stall at 15797/16234/16599/17469, matching
`warp-model.md` §3.3's table row for row).

So **`RandomBits(f) = LFSR^(f − L(f))(seed)` where `L(f)` is the number of lag frames before `f`,
and `L` counts area loads.** Both `f` (framerule-locked) and `L` (route-locked) are fixed for a
given route, so **the LFSR at every level entry is determined; spending a level's slack does not
move it.** Nothing else carried across a boundary touches physics: lives, coins ($07ed–$07ee, far
from the 100-coin 1-UP), score and the top-score digits are the only path-dependent cells, and the
game timer is reloaded from the area header on every main entry.

**Rider (and it is the interesting half):** `FrameCounter` does **not** stall on a lag frame but the
LFSR does, so the two run at different rates and their **relative phase shifts by exactly one step
at every area load**. Enemy code branches on both. This does not create a free knob on the WR's
route — but it means any route with a different number of area transitions lands on a different
`(FrameCounter, LFSR)` phase, which is the mechanism by which an off-route destination (H44) would
meet a different Bowser.

**Consequences.**
- **H9 / P2.4 (cross-level DP): closed.** There is nothing to carry, so per-level greedy is right
  and the cross-level DP has no lever to pull.
- **H2 (lag frames) reopens, sharpened.** Every area load costs exactly one lag frame. 8-4 contains
  **four** of them after its own entry (dump rows 15797, 16234, 16599, 17469) and 8-4 is
  unquantized, so **each one is worth exactly one frame off the record if it is removable**. It is
  almost certainly not — the load frame renders 12 column sets and the NMI overrun is structural,
  not marginal — but "how much work does the loading NMI actually do, and is it ever under the
  overrun threshold?" has never been measured, and one frame is the whole bar in 8-4.
- **8-4's transition budget is rigid.** Each of the four room changes costs 48 frames of
  `ChangeAreaTimer` + 43 (or 122 for a pipe-rise entry) to control + 1 lag ≈ 92–171 frames, all
  from fixed constants (`timing-model.md` §6). **8-4's only levers are movement, Bowser, and the
  ending approach** — which is what Track E points the finder at.

Reproduce: `tools/entry_state_scan.py`.

---

## E2/E3 — the finder, built; and a cap survey that reprioritises the board

### The tool
`src/fastcore/explore.c` → `build/explore` (`tools/build_explore.sh`). Archive-based exploration
on the QuickNES core: cells are a coarse projection of the state (x/4, y/8, x-speed/8,
Player_State, ScreenLeft/16, AreaPointer, GES, enemy digest), best-per-cell is kept, any cell can
be resumed at any time. No layers, so a manoeuvre that pays before it gains keeps its own cell —
the H39/F128 defect cannot occur by construction. Runs on the real emulator, so there is no model
gap and every path is core-verified as it is produced.

Two things make it aim at the right number:
- **`--seed-wr`** replays the movie's own continuation into the archive first, so the finder starts
  from an incumbent and improves it rather than discovering the goal by chance.
- **the null-coast probe**: at any frame past `--probe-x`, if the path's last button press already
  beats the incumbent, the tool releases every button and runs forward — if Mario still reaches the
  axe, that IS a shorter movie (F17). It quits the probe the moment Mario is stopped on the ground.

**Control (passes).** Seeded with the WR's own line from root 17650, the tool reports victory and a
trimmed last input of **17846** — F223's number, derived independently.

### F225 — the cap survey: the WR is at the movement cap almost everywhere
`tools/cap_survey.py`. Per level, control frames (GES 8) and how many are at the relevant speed cap
(40 running / 24 walking or swimming):

| level | ctrl | @40 | @24 | off cap | off % | biggest off-cap runs (dump row:len) |
|---|---|---|---|---|---|---|
| 1-1 | 721 | 565 | 9 | 147 | 20% | 655:47 1048:22 196:21 |
| 1-2 | 1280 | 1108 | 2 | 170 | 13% | 3571:57 3707:39 2486:38 |
| 4-1 | 1443 | 1403 | 2 | **38** | **3%** | 3981:21 4004:9 |
| 4-2 | 1064 | 853 | 14 | 197 | 19% | 6785:58 6584:37 7635:29 |
| 8-1 | 2411 | 2328 | 2 | **81** | **3%** | 10218:28 7933:21 |
| 8-2 | 1496 | 1259 | 24 | 213 | 14% | 12407:51 12289:43 |
| 8-3 | 1367 | 1330 | 2 | **35** | **3%** | 13122:21 13145:9 |
| 8-4 | 1968 | 1051 | 694 | 223 | 11% | 16500:31 16719:29 |

**What this settles.** A frame at the cap is a frame no search can improve by moving better, so a
level's improvable content is bounded by its off-cap frames — and in **4-1, 8-1 and 8-3 that is 38,
81 and 35 frames, essentially all of them the one forced acceleration after the level-start card.**
Their deficits are 9, 18 and 10. **Those three levels cannot deliver a framerule from movement at
all**, which retires the standing "search a level nobody has searched" plan (E4 as written) for
them. It also retrospectively justifies the project's concentration on 1-2 and 4-2: they and 1-1
are the only framerule levels with real off-cap content, and 1-1 is closed (F124).

8-4's own picture (`tools/cap_survey.py` plus a per-area breakdown): 1,968 control frames, of which
1,051 at the running cap and 694 at the swimming cap; every off-cap pocket inspected is a forced
pipe acceleration (96-frame vertical rise → 30-frame ramp) or a forced deceleration into a pipe.
Its two water areas ($02 rows 16515–17275 and $65 rows 17275–17493) run 527+140 frames pinned at
the swim cap of 24.

### F226 — 1-2's "intro" is not unexplored territory: it is 499 frames with input overridden
STATUS carried the claim that 1-2's opening (dump rows 1946–2486) "is not modelled at all and
Maru's 3-frame gain over the WR has to be somewhere — this is the only stretch nobody has looked
at". **That is wrong and it is now corrected.** The dump's `GameEngineSubroutine` runs over those
rows are: 1946–2108 GES 0 (163 frames, load + card), **2109–2444 GES 7 (336 frames)**, 2445–2468
GES 0, 2469–2485 GES 7, control at 2486. GES 7 is `PlayerEntrance`, and for a `PlayerEntranceCtrl`
6/7 area it runs `ChkBehPipe` → `IntroEntr`/`AutoControlPlayer`, both of which override the joypad
(`AutoControlPlayer` writes `SavedJoypadBits` itself). Mario auto-walks x 40 → 160 at speed 12 and
then stands still for ~155 frames while `ChangeAreaTimer` runs out. `timing-model.md` §7 already
had it: "Fixed **499 rows** from load to the main-area load; input is overridden."
**Consequence:** Maru's three frames are *not* in the intro; they are in the modelled body
(rows 2486–3766), which our searches have examined only from the WR's own states.

### Where this leaves the hunt
Adding it up: ~30% of the movie is rigid transition/countdown overhead (audited in
`strategy-review.md` §4 and `timing-model.md` §9), ~60% of the rest is at the movement cap, and
most of the remainder is forced acceleration. **So the record does not come from moving better.
It comes from structure: less distance (a clip or a route), fewer transitions, or a glitch.**
That is the same conclusion the 4-2 top route reached from the other direction, and it makes the
never-executed VRAM-offset measurement (F221's residual) the highest-payoff item left on Track B —
because a `WarpZoneControl` write in 1-2 removes 4-1 and 4-2 entirely (3,957 frames).

---

## E-W42 — the 4-2 wrong warp, taken to the code

The finder's second target. 4-2 is where the evidence points: it is the one place on the route
with a *distance* win already in hand (the top route's 553 vs the WR's 588, F118), and the whole
question is the price of the warp key. STATUS's "4-2 hope" thread says that price has never been
measured. Before measuring it I read the mechanism out of the disassembly, and it is now closed
at code level.

### The condition, exactly (F227)
`tools/area_data.py L_UndergroundArea2 E_UndergroundArea2` gives 4-2's own data:

- The **area-change commands** (row-$0E, which overwrite `AreaPointer` as the parser passes them):
  **page 2 col 1 → `$2F` entrance page 0** (the world-8 warp zone), **page 5 col 15 → `$42`
  entrance page 8**, page 11 col 14 → `$25`.
- The **only two enterable pipes** in the area are `page 5 col 4` (x 1344–1375 — the wrong-warp
  pipe the WR uses) and `page 13 col 6`. Everything else is a *decoration* pipe.

So the wrong warp is a race: enter the col-84 pipe **before the parser reaches page 5 col 15**.
Measured on the core, the flip happens the frame `ScreenLeft` reaches **1217**. Both traces agree
to the pixel:

| | x at pipe | ScreenLeft | rel = x − SL | AreaPointer |
|---|---|---|---|---|
| WR | 1348 | **1216** | **132** | `$2f` — warps right |
| top-route 553 chain | 1349 | 1237 | 112 | `$42` — warps wrong |

### Why 132 is hard: the complete list of ways to freeze the scroll (F227)
`ScrollHandler` (smbdis 5378–5401) is short and exhaustive. The screen does not scroll at all when
**(a)** `ScrollLock != 0`, **(b)** `Player_Pos_ForScroll < $50` (rel < 80), **(c)**
`SideCollisionTimer != 0`, or **(d)** `Player_X_Scroll + Platform_X_Scroll == 0`. Otherwise it
scrolls by Mario's movement **minus one** while rel < `$70` (112), and by the **full** amount at
rel ≥ 112.

That last clause is the whole difficulty: **at rel ≥ 112 the screen tracks Mario exactly, so rel
can never grow past 112 without one of (a)–(d).** And in 4-2's main area:

- **(a) is unavailable before the pipe** — the area's two `ScrollLockObject`s are at page 12 col 4
  and page 14 col 6, i.e. columns 196 and 230, far past the col-84 pipe.
- **(b) caps out at 112 by construction** (below 80 the screen is frozen, in [80,112) rel gains
  exactly 1/frame, at 112 it stops).
- **(d) needs `Platform_X_Scroll`, which is written only by `PositionPlayerOnHPlat`** (smbdis
  10946) — Mario standing on a *horizontally* moving platform. 4-2's only platforms are ids
  `$26`/`$27`, the vertical `MoveLiftPlatforms` elevators, so `Platform_X_Scroll` is always 0.
- **(c) is therefore the only mint, and it always costs the speed.** `SideCollisionTimer` has
  exactly one writer in the ROM: `ImpedePlayerMove` (smbdis 12318–12334), which sets it to `$10`
  = 16 frames **and on the same instruction path does `ldy #$00 / sty Player_X_Speed`.** There is
  no path that sets the timer without zeroing the speed.

**This is the proof artifact H38 asked for, and it is negative: no speed-preserving mint exists in
4-2's main area.** The WR's own mint is visible in the dump doing exactly this — at core 6782 it
is stopped at x 468 with `ScreenLeft` frozen at 357, and it is ejected +1 px per frame
(`ImpedePlayerMove`'s `lda #$01`) for ~33 frames, buying rel 112 → 132.

**What this does NOT close — and it is the live question.** The mint's *rate* is fixed at 1 px per
frozen frame, so 20 px costs ≥ 20 frames of 1-px movement; but **where** it is paid is free, and
the WR pays it at x 468 in the middle of a sprint, which also costs a full re-acceleration to the
cap. Paying it **immediately before the pipe** would cost only the 20 slow frames minus the 8 the
same 20 px would have taken at the cap (≈12 frames), plus a 1–2 frame L+R stop, and **no
re-acceleration at all, because Mario needs no speed once he is on the pipe.** Against a 22-frame
budget (553 + key ≤ 575) that is inside the line. Whether a wall-entry site exists close enough to
the pipe is a geometry question — which is what the searches below measure.

### F228 — H37 (pipe B floor-level entry) is refuted at the data level
H37 asked whether 4-2's cols 78–79 pipe can be entered at floor level, which would be a new route.
It cannot, for a reason that needs no search: that object is `page 4 col 14 row 4
VerticalPipe(**decoration**) len 6`, and `VerticalPipe` (smbdis 3837–3879) draws its top from
`VerticalPipeData` — **`$11,$10` when the second byte's d3 usage bit is set, `$13,$12` when it is
not.** `HandlePipeEntry` requires right-foot `$11` and left-foot `$10`. A decoration pipe's top is
`$13/$12` and can never be entered, however Mario arrives at it. The same argument disposes of
every other non-d3 pipe in the area, which is why the WR's col-84 pipe is not merely the best
choice but **the only enterable pipe before the `$42` command**.

### The measurement (running)
`runs/E3-w42/launch.sh` — four archives on the real core, rooted at chain steps 200 / 330 / 400 /
440 of the 553-frame top-route path, horizons 470 / 340 / 270 / 230, goal = the `$2f` commit
(`AreaPointer $2f` **and** `AltEntranceControl 1`), `--require-ram 0x750=0x2f` so any state whose
destination has already flipped is never archived, promise aimed at x 1348. Baseline: the WR
commits at core frame **7218**; a framerule needs **≤ 7205**.

---

## E-W84 — 8-4, and the scroll law that governs both levels

### F229 — the scroll law, and what it says about both attacks
From `ScrollHandler` (F227) plus the fact that the screen never scrolls left, one line follows:

> **`ScreenLeft` can never exceed `(the largest x Mario has ever reached) − 112`.**

Because at rel ≥ 112 the screen tracks Mario exactly (so rel stays 112), in [80,112) it gains one
less per frame (so rel climbs *toward* 112), below 80 it does not move at all, and leftward motion
never scrolls. rel = x − ScreenLeft, so ScreenLeft is pinned to `max_x − 112` and only a freeze
can push rel above 112 (which makes ScreenLeft *smaller*, never larger).

That single law governs the two live attacks, in opposite directions:

- **4-2's wrong warp needs `ScreenLeft` HELD BACK** (≤ 1216 at x 1348 ⇒ rel ≥ 132), which requires a
  freeze, which requires `ImpedePlayerMove`, which zeroes the speed. F227.
- **8-4's room exits need `ScreenLeft` PUSHED FORWARD** past an area-change command before the pipe
  will open on the right room — so Mario must physically reach `required_SL + 112` and then come
  back. **The overshoot distance is therefore already minimal**; only the return leg is searchable.

### F230 — 8-4 is a maze made of area-change commands, and "entered a pipe" is not a goal
`tools/area_data.py E_CastleArea6` — every area-change command in 8-4's main area, all gated on
`WorldNumber == 7`:

| at | sets AreaPointer / entrance page | meaning |
|---|---|---|
| page 3 col 8 | `$65` / 1 | **loop back to the start** |
| page 5 col 3 | `$65` / 7 | room 1 → room 2 |
| page 8 col 5 | `$65` / 1 | **loop back** |
| page 9 col 15 | `$65` / 12 | room 2 → room 3 |
| page 13 col 4 | `$65` / 1 | **loop back** |
| page 14 col 4 | `$02` / 0 | room 3 → the water room |
| page 17 col 15 | `$65` / 1 | **loop back** |

So a pipe's destination is whichever command the parser read last, and most of the time that is
"back to page 1". **The first version of these searches used `GES == 3` (a pipe was entered) as the
goal and immediately reported −54 frames in room 3 and −102 in room 2. Both were wrong-pipe
entries.** This is the F129/F131 defect in a new place, and it is the reason the runbook's rule
exists: a goal must be the thing you want, not a proxy that is cheaper to satisfy.

**The fixed goal is the destination**: `GES == 7` **and** `AltEntranceControl == 2` **and**
`Player_PageLoc == <next room's page>` **and** `Player_X_Position == 56` — i.e. Mario rising out of
the correct pipe in the correct room. Signatures and baselines, measured from the WR's dump:

| segment | root (core) | dest page | baseline (core) | WR frames |
|---|---|---|---|---|
| room 1 | 15220 | 7 | 15818 | 598 |
| room 2 | 15914 | 12 | 16255 | 341 |
| room 3 | 16351 | 0 | 16620 | 269 |
| water | 16716 | 16 | 17490 | 774 |

**All four controls pass** (each seeded WR line reproduces its own baseline). `runs/E3-w84/launch.sh`.

### Why these four
`tools/cap_survey.py` says 8-4 spends 1,051 control frames at the running cap and 694 at the
swimming cap; its 223 off-cap frames are **all** either the forced acceleration out of a pipe rise
or the deceleration/turnaround into the next pipe. Since F229 fixes the overshoot, the searchable
content of 8-4 is the return legs and the pipe approaches — and 8-4 is unquantized, so **one frame
is the record**. The water room is additionally the one 8-4 segment nobody has ever searched (696
frames, swimming, cheep-cheeps), and running on the real emulator makes the model's unvalidated
swimming irrelevant.

---

## E5 — the destination audit, and what it closes

`tools/area_data.py` over every area on the route. **Every** area-change command:

| area | level | commands |
|---|---|---|
| `E_GroundArea6` | 1-1 | p1c1 → `$42`/0 |
| `E_UndergroundArea1` | 1-2 | p2c13 → `$42`/2; p10c14 → `$25`/11 |
| `E_GroundArea3` | 4-1 | p1c2 → `$42`/6 |
| `E_UndergroundArea2` | 4-2 | p2c1 → **`$2F`/0**; p5c15 → `$42`/8; p11c14 → `$25`/11 |
| `E_GroundArea17` | 8-1 | p1c13 → `$42`/2 |
| `E_GroundArea19` | 8-2 | p7c15 → `$42`/8 |
| `E_GroundArea2` | 8-3 | **none** |
| `E_CastleArea6` | 8-4 | the maze (F230) |
| `E_WaterArea3` | 8-4 water | p4c2 → `$65`/16 (Bowser room) |

**The only cross-world destinations on the entire route are 1-2's warp zone and 4-2's `$2F`, and the
WR uses both.** Everything else is the shared bonus room `$42` or a level's own ending. F233 prices
the bonus-room detours: worth 292 frames in 1-1 (taken) and a 226–379 frame **loss** in 4-1, 8-1 and
8-2 (correctly skipped). **The route topology is forced.**

### The one new primitive found today, and its bound
A pipe's destination is read at the **load**, 48 frames after entry, and the screen keeps scrolling
through the descent off the stale `Player_X_Scroll` (which only `OnGroundStateSub`/`JumpSwimSub`
write). So a pipe can be entered *before* its destination command is parsed and still land correctly
— but the descent scroll stops the moment rel falls below 80, so

> **`ScreenLeft_at_load <= x_entry − 80`.**

For 8-4 room 3 that needs `x_entry >= 3424` against a pipe-entry window ending near 3411, so the
turnaround stands (F232); for 4-2 the same clause is what breaks F129's candidate. The primitive is
real, bounded, and on this route worth nothing — but it is worth remembering, because it is the only
lever that moves a *destination* without touching `WorldNumber`.

---

## P3.4 — the novelty sweep (`--anomaly`), and what it found

Never run before this session. `build/explore --anomaly` reports the first occurrence of each
**(class, value)** pair that the WR's own line through the same region never produces. The allowed
sets are learned automatically during `--seed-wr`, so "anomalous" is calibrated rather than guessed;
sixteen classes are watched, including the ones that would be jackpots — `WorldNumber`,
`AreaPointer`, `WarpZoneControl`, an out-of-table `Enemy_ID`, a non-zero `EnemyFrenzyBuffer`, and
`VRAM_Buffer1_Offset > 80`. Each hit dumps its path; `tools/e3_replay.py` replays any of them.

**Hits so far (1-1, 1-2, 4-2):**

| where | hit | reading |
|---|---|---|
| 1-1 | `Y above world` = 254 at x 383, and 253 at **x 436** | **F210's doorway, at column 11 on an odd page** — the H43 trigger geometry, produced away from the WR's own 8 occurrences (F211). Two pixels of Y from the exact window. Still blocked by F215's value-minting. |
| 1-2 | `WorldNumber` = 1, 2, 4, **35** | the warp zone's other pipes, plus **the Minus World** (world 36; H6 refuted at table level: `AreaPointer $01` = Water2, loops) |
| 1-2 | **`WarpZoneControl` = 5** at core 3710 | a genuinely new capability — see F235 |
| 4-2 | `PlayerSize` = 0 / `GES` = 9 at x 466 | the mushroom (H34), which the WR bumps without taking |
| 4-2 | `AreaPointer` = `$42` at x 1349 | the top route's wrong warp (F228), reproduced |
| both | `GES` = 11 | deaths |

**What F235 concludes.** Chasing the WZC = 5 hit into the disassembly settled the biggest prize on
the board: **worlds 8-7-6 is `WarpZoneControl` row 6, which `ScrollLockObject_Warp` will only write
when `AreaType == 1`, and `AreaType` is fixed at area load — so 1-2 can never legitimately produce
it.** 4-2's own warp zone is `AreaType` 2 as well and lands on row 5, `{36, 5, 36}` — the minus-world
row — which is precisely why the WR wrong-warps into `$2F` (a *ground* area) instead of using it.

So the 3,957-frame "1-2 straight to world 8" idea is closed on the legitimate path, and survives
only as H7(c): an out-of-bounds write of `$06D6` = 6, still blocked by F203's reach bound and by
F234's ceiling on the one write primitive that could reach further.

**Caveat on the logs:** the `*** WORLD 8 REACHED ***` banner fires on any `WorldNumber >= 7` and so
also fires on **35 (the Minus World)**. Read the value, not the banner.

---

## The scroll law, applied to all three gated levels (F227 / F229 / F236)

One page, because it now explains the endgame of three different levels and it is the reason the
record is hard.

`ScreenLeft = x − rel`, `ScreenLeft` never decreases, and the screen tracks Mario exactly once
`rel >= 112`. Therefore **`ScreenLeft <= max_x − rel_at_that_moment`, and `rel` can only exceed
112 through a freeze.** Freezes: `ScrollLock != 0`; `rel < 80`; `SideCollisionTimer != 0` (which
zeroes the speed); `Player_X_Scroll + Platform_X_Scroll == 0`.

| level | the gate | direction | what the WR does | verdict |
|---|---|---|---|---|
| **4-2** | destination flips when `ScreenLeft` hits 1217, so the pipe needs `ScreenLeft <= 1216` at x 1348 ⇒ **rel >= 132** | wants the screen **held back** | mints 20 px with a wall ejection at x 468, at the cost of all its speed and a full re-acceleration (~35 frames) | the only mint mechanism available (F227); measured key **~61 frames** against a 22-frame budget |
| **1-2** | the warp arms when the parser reaches column 198, i.e. `ScreenLeft` 2816 | wants the screen **pushed forward** | arrives at the arming with **rel 128** (the wall clip minted 15 px for free), so the apex is 2944 rather than 2928 | the extra 16 px is unrecoverable — trading lead costs more than it saves (F236). At its bound. |
| **8-4 room 3** | the pipe only opens on the water room once the parser has read `page 14 col 4`, i.e. `ScreenLeft` 3344 | wants the screen **pushed forward** | runs out to x 3456 = 3344 + 112 and doubles back to the pipe at 3404 | overshoot is exactly minimal; entering early and letting the descent scroll catch up is bounded by `ScreenLeft_at_load <= x_entry − 80` and falls 13 px short (F232) |

**The asymmetry that matters:** a level that wants the screen *pushed* is at its bound the moment
Mario runs at the cap, because `max_x` is forced. A level that wants it *held back* needs a freeze,
and the only freeze a player can create costs all of his speed. That is why 4-2 is the only
framerule level with a live question, and why the question is a price rather than a possibility.
