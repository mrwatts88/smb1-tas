# L7 — the novelty sweep on 8-4, and the object-slot lens it never had

**Unit:** L7 (`docs/open-threads.md`). Linux box, 2026-08-25 session 21.
**Cost:** one recompile plus a 45 s control; the sweeps themselves are five capped 6 h jobs that
queue behind the E7 archives already in flight.

## 1. The two gaps

`build/explore --anomaly` (P3.4, `runs/E6-vram/`) is the project's corner-search: from a root it
rolls out random inputs and reports the first occurrence of each **(class, value)** pair that the
WR's own line through the same region never produces. It was run once, on **1-1, 1-2, 4-1, 4-2,
8-2 and 8-3**. Two things were never covered:

**(a) 8-4 was never swept, in any of its five sub-areas.** It is the only unquantized level on the
route — every other level must save its whole framerule deficit, 8-4 pays per frame (F245 /
`tools/slack_table.py`) — so it is the one place where a single anomalous frame *is* the record,
and it is the one place the sweep never looked.

**(b) No sweep ever carried an object-slot lens.** The nearest class was 5, `Enemy_ID out of
table`, whose predicate was

```c
for(int q=0;q<5;q++) if(r[ENID+q]>0x36){ ... }      /* before this unit */
```

— **ids above the JumpEngine table only, over five of the six slots**. `Enemy_ID` is `$16-$1b` and
`Enemy_Flag` is `$0f-$14` (six slots each, F261), so slot 5 was invisible; and F258's mechanism is
`$31` (`StarFlagObject`) in a spare slot, which is **below** `$36` and therefore invisible to class
5 at any slot. The one class the sweep would have needed to see the 857-frame mechanism was the one
class it did not have. Every earlier "only mundane hits" verdict is unaffected in what it *did*
cover and silent about this.

## 2. What was built (`src/fastcore/explore.c`)

Two classes appended (17, 18 — appended, so `anom_N` file names from `runs/E6-vram/` keep their
meaning), plus class 5 widened to all six slots:

| class | fires when | calibration |
|---|---|---|
| 17 `Enemy_ID novel in a live slot` | a slot with `Enemy_Flag != 0` holds an id the reference line never parked in **any** slot in this region | learned: `ok_enid[]` collects every id seen in any slot, live or stale, so a stale byte cannot masquerade as novel |
| 18 `StarFlagObject in a slot` | **more** slots hold `$31` than the reference line ever holds here; value = the count, bit 7 = at least one of them is live | learned by **count** (`ok_nstarflag`), because the end-of-level castle legitimately parks one — so this is literally a "second star flag" detector, i.e. F258's 857 frames |

Class 5 now covers `$16-$1b`, so its hits are **not** comparable with E6's. The periodic report's
mask widened to `anom=0x%05x` (19 classes).

`tools/build_explore.sh` now builds to a temp file and `mv`s it into place: a rename is atomic and
leaves a running search's mapped inode alone, so rebuilding mid-search neither fails with ETXTBSY
nor disturbs a job in flight. `OUT=` builds a second binary alongside.

## 3. The roots (F265)

From `tools/ram_trace.py data/wr/fceux_wr.ram 15050 17868 GameEngineSubroutine --changes`, 8-4's
five sub-areas, in WR dump rows (= core frame + 1):

| sub-area | load (F264) | control (GES 8) | leaves by (GES 3 pipe / 2) | length | root used | horizon |
|---|---|---|---|---|---|---|
| room 1 | 15058 | **15224** | 15748 | 524 | 15210 | 800 |
| room 2 | 15796 | **15918** | 16185 | 267 | 15905 | 550 |
| room 3 | 16233 | **16355** | 16550 | 195 | 16342 | 500 |
| water room | 16598 | **16720** | 17416 | 696 | 16707 | 950 |
| Bowser room | 17468 | **17590** | axe / 17868 | 278 | 17577 | 400 |

Roots are control − ~13 (inside the load window), the same convention E6 used (8-3: control 13123,
root 13110). Horizons run each sub-area plus its transition into the next; the Bowser root's
horizon reaches the end of the game, so **that job's default goal (`OperMode == 2 && World >= 7`)
is live** and it doubles as an H1 ending-input probe — it prints `last_input` against the WR's
17846 and writes `best_*.path` if it ever beats it.

## 4. Control (45 s, `runs/L7-w84/smoke/`)

```
systemd-run --user --scope -q -p MemoryMax=400M -- ./build/explore … --root 17577 --horizon 400 \
  --max-addr 0x300 --max-weight 20 --prog-fw 1 --anomaly --cells 4000 --rollout 6,50 \
  --enemycell 0 --xcell 8 --ycell 16 --spdcell 16 --relcell 32 --seed 85 --secs 45 --report 15
```

- `anomaly calibration from the WR line: 2 GES / 1 OperMode / 1 World / 1 AreaPointer /
  3 PlayerState / **6 Enemy_ID** values are normal here` — the new table calibrates.
- `GOAL victory=17865 last_input=17846 (WR 17846)` — the seeded WR line reaches the ending from
  this root, so the goal metric is live and reproduces the WR exactly.
- 848 goals / 3,393 rollouts / 0 deaths in 45 s; hits in classes 1, 6, 14, 15 (`GES = 11`,
  `EnemyFrenzyBuffer = 21`, `SecondaryHardMode = 1`, `DuplicateObj_Offset = 3`), all inside the
  known sets — `$06CB = $15` is one of F261's six legal frenzy values, not an injector.
- No class 17/18 hit in 45 s, which is the expected null for a control.

## 5. What is running

`runs/L7-w84/launch.sh` (committed; carries the roots, the lens description and the read-out
recipe). `r5` (Bowser room) started immediately at `--cells 40000` under `MemoryMax=800M`, because
that was the RAM the box had spare with three E7 archives in flight. The other four are **queued**:
a `WAIT=1 WAITN=1 SKIP=r5` instance of the same launcher polls every 60 s and fires them at
`--cells 80000` / `MemoryMax=1500M` as soon as only one `explore` remains (i.e. when E7 exits,
~2 h). If that waiter is gone, just run the launcher by hand.

**Read the results:** `grep ANOMALY runs/L7-w84/*.log`, then replay any hit with
`tools/e3_replay.py runs/L7-w84/anom_<class>_f<frame>.path`. Classes 17 and 18 print
`*** OBJECT-SLOT ANOMALY (F258 class) ***` and `*** SECOND STAR FLAG — F258'S 857 FRAMES ***`.
Priced: a class-18 hit that is **live** is 857 frames (1,329 with the music, F259); a class-17 hit
is worth reading but is not priced in advance. On `r5` only, a `best_*.path` with
`last_input < 17846` is a record on the ending-input coast (H1).

## 6. What this unit does not claim

The sweep is a corner search, not a proof: a dry run says the rollout policy did not reach an
anomalous state in 6 h from that root, nothing more. It also does not close gap (b) for the five
levels E6 already swept — **re-running E6's six roots with the object lens is a follow-up**, same
binary, same launcher shape, and cheap.

---

# L9 — the sweep read out (2026-08-26, session 22)

**7 of 10 roots complete, ~2.48 billion simulated frames. No class-17 or class-18 anomaly anywhere.**

## Per-root results

| root | sub-area | seed | cells | rollouts | frames | goals | deaths | `anom` mask |
|---|---|---|---|---|---|---|---|---|
| `r1` (Mac) | room 1 | 81 | 80k | 16,967,724 | **440.74M** | 0 | 1,066,361 | `0x15002` |
| `r2` (Mac) | room 2 | 82 | 80k | 16,594,073 | **434.59M** | 0 | 591,083 | `0x17042` |
| `r4` (Mac) | **water** | 84 | 80k | 16,181,191 | **420.28M** | 0 | 299,792 | `0x04003` |
| `r3s100` (Mac) | room 3 | 183 | 80k | 16,657,395 | **449.23M** | 0 | 1,015,634 | `0x17053` |
| `r5s100` (Mac) | Bowser | 185 | 80k | 12,138,373 | **322.41M** | 184,198 | 581 | `0x1c043` |
| `r3` (Linux) | room 3 | 83 | 80k | 9,714,660 | **263.67M** | 0 | 482,872 | `0x17053` |
| `r5` (Linux) | Bowser | 85 | 60k | 5,486,591 | **146.25M** | 144,458 | 53 | `0x1c043` |

Still running (Linux, launched by the armed hand-off at 01:33, end ~07:33): `r1s200` (seed 281),
`r2s200` (282), `r4s200` (284) — second independent seeds for the three rooms that had only one.

## The two priced classes did not fire

**Not one root's mask has bit 17 or bit 18 set.** No mask exceeds `0x17053`, and bit 17 is `0x20000`.

- **class 18** — `*** SECOND STAR FLAG ***`, a slot holding `$31` beyond the reference line. Priced at
  **857 frames** (1,329 with the music, F259). **Zero hits.**
- **class 17** — a novel `Enemy_ID` in a *live* slot, calibrated. **Zero hits.**

## Every class that did fire, and why each is mundane

Triaged rather than assumed — two were run down in the ROM and one was core-replayed:

| class | what fired | verdict |
|---|---|---|
| `GES = 6` / `GES = 11` | GameEngineSubroutine 6 and 11 | **Deaths.** The GES jump table (smbdis 5478-5490) is index-ordered: 6 = `PlayerLoseLife`, 11 = `PlayerDeath`. The seven roots logged ~3.46M deaths between them, so these are the single most expected values on the board |
| `GES = 3` | vertical pipe entry | Normal 8-4: every room transition is a pipe |
| `position jump = 255`, `AreaPointer = 229` | the room-2 **loop-back pipe** | Already known and already priced — it is the same false positive that poisoned L4's goal (F274) |
| `ScrollLock = 1` | scroll locked | Normal in 8-4's rooms |
| `Y above world = 250..255` | Mario's Y high byte | The tall room 3 and the water room; also the death plunge |
| `SecondaryHardMode = 1` | hard-mode flag | Normal past world 5 |
| `EnemyFrenzyQueue / Buffer = 20, 21, 24` | `AreaFrenzy` spawns | **The game's own spawner, not a glitch.** `FrenzyIDData` (smbdis 3604) is `FlyCheepCheepFrenzy, BBill_CCheep_Frenzy, Stop_Frenzy`; core replay of `anom_13_f16434.path` shows three enemies of ID `$14` appearing at frame 16434 while Mario is mid-jump at x 3290, speed 40. Flagged "novel" only because the WR's own line does not have a frenzy active there |
| `DuplicateObj_Offset = 3` | enemy-slot duplication | Bowser's rear half and the **fifth firebar part** (smbdis 8531, 9750, 10274). 8-4 is full of firebars |

## H1 (the ending-input coast) is also negative from this root

`r5` and `r5s100` both root at 17577 with a horizon reaching past the axe — the only roots whose horizon
covers the ending, and therefore the only direct test of F223's untested *approach*. Both finished with
`best_last_input=17846`, **exactly the WR's own last input**, across 468M frames. No earlier last input
exists in the searched set.

## Verdict

**Dry across every completed sub-area of 8-4, at ~2.48 billion frames.** Stated at the width the evidence
supports: this is a **statement about the rollout policy from these seven roots**, not a proof that no
anomalous state exists in 8-4. What it does close is the specific, priced hypothesis the unit was built
for — F266's blind spot (the object-slot lens that no earlier sweep carried) has now been applied to all
five of 8-4's sub-areas, on two independent seeds for four of them, and **the star-flag class it was built
to see never appeared.**
