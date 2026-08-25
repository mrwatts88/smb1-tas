# Staged: the wall-face census, the cap premise, and an F224 correction

**Written 2026-08-25 from the Mac (session "mac") while the Linux session was live and committing
every few minutes.** Deliberately staged as its own file rather than edited into `docs/facts.md`,
`docs/hypotheses.md` or `STATUS.md`, because those were being rewritten concurrently (c433e68 and
four others landed inside ten minutes). **Next session: merge these into the real ledgers and delete
this file.** Numbers below were free as of commit c433e68; renumber if taken.

Provenance: the user, in conversation, asking three questions in order — "why are we not finding new
clips, has every wall been tried?", "has anything been done on cross-level effects?", and "do we know
the boot/Start presses are optimal?". The first turned out to be open and enumerable. The second and
third turned out to be closed, and are recorded in §4 so nobody re-runs them.

---

## 1. H46 — the wall-face census: the F80/F93 clip primitives have never been applied route-wide

**Hypothesis.** SMB1's two known collision-entry primitives are *general mechanics*, not site trivia,
and the set of solid faces on the route that admit them has never been enumerated. At least one
unexploited face exists.

**The primitives, both already established in this repo at code level:**

- **F80 / H33 — the walk-through.** `DoPlayerSideCheck` returns after the *first* side point that
  touches any metatile. Standing Mario's side points are at x+2 and x+13. Once the x+2 point is
  inside a solid run, x+13 is never tested and Mario **walks through at full speed**. The WR itself
  does this from x 481 to 824 in 4-2 (dump rows 6804–6960).
- **F93 — the foot-check entry.** A Left press makes `Player_MovingDir` LEFT, so the foot-check
  impede pushes Mario **+1 px into** the wall instead of out, while the standing side impede is
  skipped by hopping. Kept sub-speed then drifts him +0.95 px/frame until the side point is inside.
  Costs speed (`ImpedePlayerMove` zeroes it) and therefore mints scroll offset (F120).

**Why this is live right now, not speculative.** E7 (c433e68) worked out 1-2's endgame budget by hand
and landed on exactly this: the lever there is a **speed-preserving walk-through** rather than a
speed-killing clip, worth `~13 + (clip frames saved)` against a deficit of **8**. That is one site,
found by algebra on one level. **The primitive is general; the census asks where else it applies.**
E7 does not supersede this — it raises its prior.

**What is actually untested.** H10 (8-4 exhaustive incl. wall clip), H12 (L+R clip semantics), H18
(big-Mario clip geometry) are all still marked untested. Tested to date: 1-2's clip (F143/F144),
8-4's pipe clips (F66), and one failed attempt at 4-2's pipe B (H37).

**Why it stalled — this is a rooting problem, not a clip problem.** Read H37's status line: the pipe-B
test "still needs a root on the floor in front of pipe B", and the ladder that ran reached it not at
all — "every one slams pipe A's face at step 469" (F117). Every tool in the repo is a long-horizon
search from a fixed root, so testing a face at x 1200 requires *searching your way there* with a valid
chain first, and that search fails for reasons unrelated to the clip under test. The per-site question
is tiny — a handful of frames in a few-pixel window — but it is gated behind an expensive and
unreliable approach problem.

**The fix, already in the repo.** F50: savestate = template + patched RAM. **Root directly at each
face** — from a WR state or synthetically — instead of searching to it. Hundreds of sites x a small
local exhaustive search is affordable; it converts "maybe every wall has been tried" into a table with
a verdict per face.

**Method.**
1. Enumerate every solid-metatile face on the route from `tools/area_data.py` over the nine area
   labels already decoded for F233 (`E_GroundArea6/17/19`, `E_UndergroundArea1/2/3`, `E_GroundArea3`,
   `E_CastleArea6`, `E_WaterArea3`). Keep faces Mario passes within reach of.
2. For each face, build a root savestate immediately in front of it (F50), sweeping the small local
   state box: x subpixel, y over the standing/jumping/falling band, x-speed, `Player_MovingDir`.
3. Local-exhaustive over a short horizon with the F80 and F93 primitives as the input alphabet
   (including L+R, per H12).
4. Verdict per face: admits-walk-through / admits-foot-entry / refuses. Core-verify positives only
   (per the session-18 doctrine change).

**Run it at BOTH hitboxes — this folds in H18 and is nearly free.** `DoPlayerSideCheck` takes its
block-buffer adder offset from `$eb`, which is indexed by player size, and the routine explicitly
checks *two halves* of the player ("run code until both sides of player are checked", smbdis
`SideCheckLoop`). So **which rows the side points occupy is hitbox-dependent**, and therefore which
faces admit a walk-through is hitbox-dependent. See §3: the WR is small Mario for the entire run, so
the big-Mario side-point geometry has never been tested anywhere on the route. Prior stays low — the
mushroom costs frames, the growth animation freezes the player, and big Mario cannot fit 1-tile gaps —
but the census makes it a flag rather than a separate experiment.

**Why the finder will not stumble into this on its own.** `src/fastcore/explore.c:343-344` builds the
cell key from `(x/xcell, y/ycell, (speed+128)/spdcell, PSTATE&3, rel/relcell, SCTIMER!=0, ...)`.
**There is no subpixel dimension at all**, and the live jobs run `--xcell 8 --ycell 16`. Clip windows
are 1–2 px and subpixel-dependent: F93's entry works via a kept sub-speed drifting +0.95 px/frame,
and F119's legal band is Y in [72,78) — a 6 px window living entirely inside one 16 px y-cell. Note
that the one bucketed beam that *did* work on 4-2 (F127) bucketed on scroll-offset x y-band x x-speed
x **subpixel**; subpixel was load-bearing there and is absent here. The finder is well-built for
scroll-minting (`rel` is a cell dimension — correct call) but at these settings it cannot resolve the
states clips depend on.

**Falsification.** A completed census with every face marked "refuses" at both hitboxes closes H46,
and is a much stronger statement than anything currently on the board about clips.

---

## 2. H47 — an over-cap forward displacement mechanism exists (the premise every closure rests on)

**Hypothesis.** Some mechanism moves Mario forward faster than the running speed cap (40 subpixels/
frame) — a collision push chain, a platform/lift carry, an enemy interaction, a coordinate wrap.

**Prior: low.** But this is worth a numbered entry because **its refutation is the unstated premise of
every "closed" verdict on the board**, and that premise is currently implicit across a dozen separate
facts rather than stated once.

Every one of these rests on an x-table lower bound whose per-frame progress is priced at the cap:

| Verdict | Source | Dies if H47 holds? |
|---|---|---|
| 1-1 closed end to end | F124 | yes |
| 4-1 / 8-1 / 8-3 cannot deliver a framerule from movement | F225 | yes |
| 4-2 closed both routes | F122 / F123 | yes |
| 8-4 closed on movement | F232 (movement half; the topology half survives) | partly |
| 1-2's loss map and the 54-frame figure | F152 / P2.2f | yes |

The bounds are *loose* in the right direction for most purposes (F153: the x bound ignores walls, so
it under-prices time and is admissible) — but loose-because-it-ignores-obstacles is only admissible
while nothing beats the cap. **If any over-cap displacement exists, all of the above become
inadmissible simultaneously**, and the board reopens.

**Known partial answers already in the repo, which is why the prior is low:** F227 enumerates every
way to freeze the scroll and finds only `SideCollisionTimer`, whose sole writer zeroes
`Player_X_Speed` on the same path; F120 establishes that collision-push displacement moves the player
*without* feeding the scroll, which is displacement but not speed. F231 records a genuine coordinate
wrap (8-4 room 1, x 1270 -> 261) but it is level-design looping, not a gain.

**Action:** no new search. State the premise once in `STATUS.md` next to the closure list, so that if a
mechanism ever turns up it is immediately obvious what it invalidates.

---

## 3. Correction to F224, and a new measurement

**F224 as written contains an error.** It says `InitializeArea` clears `$0000-$074b` and that "above it
only lives/coins/score/top-score are path-dependent". That is incomplete:

- `PlayerSize`   = **$0754**  (smbdis.asm:226)
- `PlayerStatus` = **$0756**  (smbdis.asm:227)

Both are above `$074b`, both are path-dependent, and **both change Mario's collision box** — i.e. they
are a cross-level channel that survives the area init *and* touches physics, which is exactly the
class F224's sentence denies exists.

**The H9 refutation itself survives untouched.** H9 was about RNG and framerule phase, and F224's LFSR
argument is independent and correct: `RandomBits` stalls exactly once per area load, so the LFSR at any
later entry is a pure function of (entry frame, area-load count), and spending a framerule's slack
cannot move it. Only the parenthetical needs fixing — before someone later cites F224 as "nothing
crosses a level boundary".

**New fact (proposed F238) — the WR runs the entire game as small Mario.** Census of
`data/wr/fceux_wr.ram` over all 18,268 frames:

- `$0756` (`PlayerStatus`): **0 on 18,264 frames**; 255 on 4 (uninitialised boot garbage).
- `$0754` (`PlayerSize`):   1 (small) on 18,235 frames; 0 on 29 (boot, pre-init); 255 on 4.

HappyLee never powers up, anywhere, once. **Consequence:** big-Mario side-point geometry is unexplored
across the entire route, which is the input to H46's second hitbox above.

Reproduce: read byte `$0754`/`$0756` at stride 2048 over `data/wr/fceux_wr.ram`.

---

## 4. Checked and already closed — do not re-run these

Recorded so the next session does not spend a unit rediscovering them.

- **Cross-level carryover: closed.** H9 refuted by F224 with a real artifact
  (`tools/entry_state_scan.py`). `InitializeArea` clears `$0000-$074b`; the LFSR stalls once per area
  load; the game timer reloads from the area header. No lever. (Subject only to the §3 correction,
  which does not restore one.)
- **Framerule-phase manipulation: mostly closed.** H3's pause lever is dead by F62 — pause freezes
  ITC, `FrameCounter` and all game logic but *does* step the LFSR, so it shifts RNG phase relative to
  everything else, not framerule phase.
- **Boot / Start / pre-level: closed by F31, confirmed here.** The title menu accepts Start from row
  34, and **every Start row 34-43 yields control on the same row 197** — a 10-frame flat equivalence
  class. 1-1's control start is fixed by the boot ITC phase (7 boot lag frames), not by the Start
  frame. Verified independently against `data/wr/wr_inputs.bin`: the WR's first non-zero input is
  frame **41**, value `0x8` (Start), nothing before it. Pressing Start earlier gains exactly zero.
- **Lag manipulation: closed by F30.** All 24 lag frames are boot (7), the Start press (1) and one per
  area load (16). **There is no in-level lag in SMB1**, so there is nothing to manipulate; and the
  area-load lag frames are topologically forced by F232/F233.
