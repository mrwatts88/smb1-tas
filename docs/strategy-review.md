# Strategy review — why the record has not fallen, and what changes

**Written 2026-08-25 (session 18), at the user's request, outside the normal unit loop.**
Inputs: PLAN/PROCESS/STATUS in full, `docs/hypotheses.md`, `docs/oob-audit.md`,
`docs/timing-model.md`, `docs/warp-model.md`, the session-17 log entries from both parallel
sessions, and four routines read directly out of `data/disasm/smbdis.asm`.

**This document supersedes the priority order in `PLAN.md` §6 and `docs/decisions.md`
(2026-08-24, "the 8-4 campaign") wherever they disagree. STATUS "Next up" is rebuilt from
§5 below.**

---

## 1. Is 17,868 optimal? No — and here is the honest split

Roughly **3-in-4 that a sub-17,868 movie exists**, with nearly all of that probability in 8-4.

The case *for* optimality is real but narrower than it is usually stated. zdoroviy_antony's 2019
subpixel-perfect rewrite landing on exactly 17,868, MrWint's optimiser tying the WR on all ten
segments it solved (F66), humans matching the TAS framerule in seven of eight levels — every one
of those optimised **segments with pinned endpoints**. They agree with each other because they
share a decomposition, not because they searched the same space.

The case against:

1. **8-4 needs one frame out of 2,810 unquantized ones** (H24). It is the one level humans do not
   match. It has a water room with no solved optimum, a Bowser fight whose RNG is not in the model
   at all, four sub-area transitions, and an ending-coast objective nobody has jointly optimised.
   Nobody has ever searched it whole.
2. **The one time this pipeline looked at a route nobody had pinned it found 35 frames**
   (4-2 top route, 553 vs 588, F118). That is what an unoptimised route looks like when a machine
   hits it. 4-1, 8-1, 8-2, 8-3 and all of 1-2 past its 71-frame opening have never been
   exhaustively searched by anyone, MrWint included.
3. **Most "closed" verdicts in this repo are beam-grade.** F122 was written up as structural
   infeasibility and was refuted two sessions later (F127/F128). F123's closure of 4-2's bottom
   route rests on the identical defect and has never been re-run.

The record is **unbeaten, not proven**. The difference is where the work is.

---

## 2. Diagnosis — five failure modes, all visible in this repo's own record

**(a) Every decomposition is a first-arrival gate, and a first-arrival gate deletes exactly the
manoeuvres that beat a fifteen-year-old route.** A search rooted on a WR state and goaled on a WR
milestone can only find improvements that are monotone the whole way. It structurally cannot find
"pay 19 frames of held Left now, gain 30 later" — which is literally what F127 found once the gate
was removed. This project has rediscovered the same fact four times: F115, H39/F128, F143 (a
33-vs-42 arrival at 1-2's clip gate, worth nothing because its continuation was pruned at layer 1),
and H42. Each time it is recorded as a local lesson, and the next unit builds another gated search.
**This is why a 2011 route survives. HappyLee decomposed, MrWint decomposed, we decompose.**

**(b) The bottleneck is the state space, not the bound — settled this session by the other
session.** `P2.2f-bound` §41: from prefix 200 in 8-4 room 2, with the bound only **4 frames loose**,
the frontier is **36.7M states wide by layer 24** and growing ×2.0/layer. F98's law holds and its
constant is brutal: slack 4 buys 24–30 layers; the open seam is 197 frames out. **No bound puts a
deep question in exhaustive reach.** The bound work is still worth having (14 → 8 at 8-4's airborne
approach, 6,942 audit checks, 0 violations) because it prunes late layers, but it is not the
unlock, and the campaign to make it one is retired.

**(c) The searches optimise the wrong scalar.** Time is worth zero inside a framerule (H41, written
down, never implemented). In 1-2 the binding quantity is not Mario's x but `ScreenLeft` — a property
of where Mario has *been* (F144: three real frames found at the clip and refunded to the scroll;
F152 gives the exact incidence). In 8-4 the objective is not the axe frame but the **last input**
frame (F17). Three levels, three objectives, one heuristic.

**(d) Effort went where the frames are not.** Track B spent a session-chain rigorously establishing
that the game's only OOB write primitive can write exactly `{$00, $23, $c4}` (F215) — good work,
hunting an ACE in the one game whose ACE is already published and needs a cart swap. Meanwhile the
two largest non-movement pools on the route were never audited: **1,492 frames of time-bonus
countdown** (370+340+200+338+244 across the five flag levels) and **~700 frames of "WORLD x-y"
card** (six main entries × (≈160 − 43)). Both are audited in §4 below. Both are rigid. That is
~2,200 frames converted from *untested* to *closed at code level* for twenty minutes of reading —
and it is the template: **audit the big pools before searching the small ones.**

**(e) The process rewards turnover over depth.** A unit is 1–3 hours and must end in a documented
verdict. The cheapest way to produce a verdict on schedule is a beam. That is the mechanism behind
"we keep abandoning half-explored ground for new ground".

---

## 3. The doctrine change (user, 2026-08-25)

> "I don't need proof or exhaustiveness as a rule. I don't care about those, I just want a record."

This is a real change and it re-ranks almost everything:

- **Exhaustive proof runs are no longer a deliverable.** Runs like 1-1's end-to-end closure (F124)
  and 8-4 room 2's dry rungs (F139) are no longer the point. Do not spend a session proving a
  negative.
- **A beam is a legitimate finder.** The objection to beams was never that they are unsound as
  *finders* — it is that a beam *dry* is not a verdict. Under the new doctrine we simply stop
  writing verdicts. Beams, stochastic search, annealing, restarts: all fair.
- **The hard constraint that remains is truth about a positive**: anything that claims to beat
  17,868 must replay on the real core and then in two emulators (PROCESS evidence standards).
  Positives get verified; negatives get shrugged at.
- **`docs/hypotheses.md` keeps its "refuted requires a proof artifact" rule** so nothing gets
  falsely closed — but "parked, not worth the compute" becomes the normal resting state, and
  that is not a failure.

---

## 4. Two audits done while writing this (the big pools)

**The time-bonus countdown — rigid.** `AwardGameTimerPoints` (smbdis 10487) subtracts one timer
unit per frame until `GameTimerDisplay | +1 | +2` is zero; it is on the critical path to
`StarFlagTaskControl` = 5 (F27). Shortening it requires lowering `GameTimerDisplay` ($07F8–$07FA).
Its only writers are `Entrance_GameTimerSetup` (2833: `GameTimerData,y`, y = 2 header bits, 4-entry
table, in bounds), `RunGameTimer` (6440), and `AwardGameTimerPoints` — and **every
`DigitsMathRoutine` call site passes a constant Y** ($0b / $11 / $23; 7089, 7107, 6465, 10500,
10509). `DigitModifier` ($0134–$0139) is zeroed at the end of every call (`EraseDMods`). Neither
known OOB write primitive reaches $07F8 — the block buffer tops out at $06CF (F203) and the
`VRAM_Buffer1` overflow reaches $0301–$0400 (F218). **~1,492 frames, unreachable.**

**The intermission card — rigid, with one live question.** `DisplayIntermediate` (smbdis 1540)
skips the card only when `AltEntranceControl != 0`, or when `DisableIntermediate != 0` **and**
`AreaType != 3` (castles always show it — "possibly residual" in the comment). Warp pipes force
`AltEntranceControl = 0` when WZC ≠ 0 (`warp-model.md` §3.3) and area init clears
`DisableIntermediate` (2733); the flag is set only by `IntroEntr` (5514), gated on the *destination
area's* own `PlayerEntranceCtrl` = 6/7 header bits. **~700 frames, rigid per destination — but the
header bits are a ROM constant we can read.** That gives a new and never-applied criterion for
ranking wrong-warp destinations (H44): an area whose header says "enter from a side pipe" is
entered **without a card and unquantized**. Cheap to tabulate with `tools/area_data.py`. Filed as
E5 below.

---

## 5. The plan — Track E, "the finder"

The unifying move: **stop trying to make the exhaustive search reach further, and build a search
whose shape can hold a trade.** Under §2(a) and §2(b) that is not a bound problem and not a
frontier problem; it is an algorithm problem, and the algorithm class that solves exactly this
problem shape — deceptive reward, must-go-backwards, huge state space, cheap simulator — is
**archive-based exploration (Go-Explore)**.

### E0 — the substrate is already built
`build/harness` is a headless libretro QuickNES driver: **15.0k fps/instance, 104k fps on 12
threads, state 12,792 B, save+load 2.5 µs** (F46), and `ram_oracle.c` already does
serialize/restore/probe. Running the finder on the **real emulator** rather than the model removes
the entire model-gap risk class that has cost this project three units (F147, F149, F150) — and any
path it finds is core-verified by construction.

### E1 — S7, the free-knob check (small, first)
Is level-entry state a pure function of the entry frame? If yes, the game decomposes exactly into
seven framerule lotteries plus 8-4, per-level greedy is right, and H9/P2.4 close forever. If no —
if the LFSR or any timer phase carries — then the framerule levels' slack (3–20 frames each, free)
becomes a **zero-cost knob on 8-4's Bowser and cheep RNG**, and 8-4 is the unquantized level. F62
already shows the LFSR and `FrameCounter` are not welded together. One afternoon against
`data/wr/fceux_wr.ram`.

### E2 — the last-input reformulation of 8-4 (small, aims at the one number)
The movie ends at the last input (F17): the WR's is frame 17848 and the axe is 19 frames later.
**Reformulate 8-4's endgame as: find the earliest frame after which the null-input continuation
still reaches the axe.** That is a different question from "reach the axe fast" — a *later* axe
touch with a longer coast is a strict win. Start with the free test (truncate the WR's own input
and see how far back the game still finishes), then search the last ~120 frames with the coast as
the objective. Airborne frames preserve horizontal speed that ground friction eats, so a final jump
whose last A-press is the last input is the shape to look for.

### E3 — the Go-Explore finder on the core (the main engineering item)
Archive keyed on a coarse cell — (x band, y band, x-speed band, scroll-offset band, block/enemy
digest, frame band). Per cell keep the best state under the *level's own* objective. Loop: pick a
cell (weighted to under-visited and to recently-improved), restore, roll out 15–60 frames of
sampled input, insert. No bound, no frontier, memory bounded by cell count. This holds
"pay first, gain later" natively — the paid state stays in its cell. Objectives per level:
8-4 → last input frame; 1-2 → `ScreenLeft` / `warp_armed`; flag levels → grab frame.
Target 8-4 first (unquantized ⇒ one frame is the record).

### E4 — point the finder at territory nobody has pinned
In order of remaining deficit and of how unexplored they are:
**1-2's 540-frame intro** (fceux rows 1946–2486, never modelled, and Maru's 3-frame advantage over
the WR is somewhere in 1-2), **8-3** (7 with FPG), **4-1** (9), then 8-1/8-2. Whole regions,
seam-free, no intermediate goals.

### E5 — the destination table, re-ranked (Track B's only live thread)
Tabulate every reachable area by: card / no card, quantized / not, timer reload, and distance to
8-4's axe. H44's question ("an off-route destination may be faster") has never been asked with the
card-and-quantization columns filled in. Cheap, and it is the only Track B work with a frame
attached to it.

### Retired / demoted
- **`P2.2f-bound` as an unlock** — retired on the other session's own §41 evidence. Keep the
  Blocker term that is already built and audited; do not extend it.
- **Exhaustive proof ladders** — retired as deliverables (doctrine, §3).
- **Track B's ACE line** — parked. F215 closed it at the capability level; E5 is what is left.
- **1,492 frames of countdown / ~700 of card** — closed at code level, §4.

---

## 6. Process changes

1. **A completeness ledger, not a verdict log.** One table: region × (what was searched, with what
   objective, how deep, best found). No "closed" column. This turns "what did we abandon?" from
   archaeology into a lookup, which is the specific complaint that started this review.
2. **Units may produce no verdict.** E3 is multi-session engineering with nothing to write in Done
   until it lands. That is allowed.
3. **Long finders run detached under a memory cap and are checked, not babysat** — unchanged from
   the runbook, but now the normal mode of work rather than the exception.
