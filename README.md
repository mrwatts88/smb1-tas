# smb1-tas

An attempt to beat HappyLee's 2011 "warps" TAS of *Super Mario Bros.* — TASVideos
[#1715M](https://tasvideos.org/1715M), **17,868 frames** — by exhaustive and novelty search instead of
hand-optimisation.

**It failed. The record stands.**

This repository is the full record of the attempt: **241 verified facts, 50 hypotheses, 37 experiment
write-ups, 71 sessions**, and the logs of searches totalling **billions of simulated frames**. It is
public because the negative results are specific enough to be useful, a couple of the findings are
interesting on their own, and the failure modes were more instructive than the successes.

---

## Why this is hard

Seven of the eight levels on the route are **quantized by framerules**: the game only advances the
level-exit bookkeeping every 21 frames, so saving 1–20 frames in such a level is worth **exactly
zero**. You must save the whole remainder or nothing. That single fact is why most of this project's
work terminates in "we found real frames and they bought nothing."

**8-4 is the exception.** It has no flagpole and no framerule, so there **one frame is the record**.
Unsurprisingly, that is where the project spent its last and largest effort.

---

## What the attempt established

The route loses **290 frames to geometry** — the entire budget any movement-based improvement could
draw on. Every priced target inside it was searched, where it was priced:

| level | result |
|---|---|
| **1-2** | **Closed by arithmetic, not by a dry search.** Its ceiling is **3** frames against a requirement of **8**. An exhaustive rung puts the wall clip at exactly 3; Maru370's hand-made "perfect 1-2" independently lands on the same 3; everything else in the level was verified optimal. 3 < 8, so no route through 1-2 crosses its framerule. |
| **8-2** | The largest priced site (114 frames). Two 6-hour archives, **~903M frames** — both finished one frame *worse* than the WR. |
| **8-4 exit pipe** | **~382M frames**, 291 pipe entries, none earlier than the WR's. |
| **8-4 novelty sweep** | All five sub-areas, two independent seeds each, **~3.25 billion frames**, with an object-slot lens no earlier sweep carried. The 857-frame anomaly class it was built to find never appeared — and the two seeds **converged bit-for-bit** on the same anomaly inventory, which is a stronger negative than a single dry run. |
| 1-1, 4-1, 4-2, 8-1, 8-3 | closed or proven to have no available loss |

**What is deliberately *not* claimed: that the record is unbeatable.** One hypothesis class — an
over-cap forward displacement mechanism, priced at up to ~50 frames — has exactly one known instance
and it is clamped away. That is **un-enumerated, not refuted**, and `STATUS.md` says so at the top so
nobody inherits a closure the evidence does not support.

---

## Two findings worth reading even though neither paid

**Left+Right indexes past the end of a table and teleports Mario 6,406 pixels.**
`PlayerFacingDir` is 1 (right) or 2 (left) — but pressing **both** makes it **3**, a value no single
button produces. `PutPlayerOnVine` uses it to index two **2-byte** tables. With facing = 3 both reads
land one byte past the end, on the adjacent table, and Mario's page location jumps by 24 pages. It was
measured on the real emulator, not just read: x 3,065 → 9,471. It doesn't pay — the next frame's
on-screen clamp undoes it, and 8-4 has no vine — but it is real, and it re-priced an entire class of
hypothesis. (F268–F270)

**The water speed cap misses unlocking by exactly one unit.**
Water runs four speed caps. Swimming is capped at **24**, and the game's fast 40-cap unlocks when
`Player_XSpeedAbsolute >= 25`. One short. Poking the value to 25 for 60 frames makes the speed climb
24 → 26 → … → 40 and *stay* there, worth **≈259 frames** in 8-4's water room. Then all eight writers of
`Player_X_Speed` were enumerated and none can reach 25 while swimming — so the door is real, measured,
and provably shut. (F271)

---

## Failure modes that generalise

These cost the most and are the most transferable:

- **A search key that cannot represent its answer fails *silently*.** Two independent negatives were
  produced by a beam keyed on five state fields when the quantity searched for depended on six. The
  runs terminated normally and reported clean dries. Widening the search would never have helped.
- **A proxy goal manufactures fake records — and can suppress real ones.** A pipe-entry goal that
  wasn't position-qualified fired on a *loop-back* pipe 112 frames "early". Because the search only
  records goals that improve on the incumbent, that one false hit made every genuine candidate
  permanently unreportable while the run kept printing healthy progress.
- **Two launchers for one job drift, and the failure is silent under-delivery, never an error.** Twice
  in one day: a 25%-undersized default, then an ignored `SKIP` that spent two machine slots on
  byte-identical duplicate work.
- **Prose is not a queue.** Work described in a document but never entered into the queue the process
  actually reads does not get done. Three separate pieces of real work were nearly lost this way.
- **Believing a well-established outside number can *close* a question rather than open it.** Treating
  a published community result as an unverified claim kept a level artificially open; taking it at face
  value is what proved the level shut.

---

## How it's organised

| path | what |
|---|---|
| **`docs/open-threads.md`** | **start here** — every thread, closed / dry / parked, each with a fact number and an artifact. The live board is empty. |
| `docs/facts.md` | the fact ledger. Each entry is **V** (verified here, citing the script or experiment) or **S** (sourced from the community, treated as a claim to verify) |
| `docs/hypotheses.md` | the ideas ledger. Nothing is marked *refuted* without a proof artifact — a search record or a code-level argument |
| `docs/experiments/` | one write-up per experiment: setup, exact command, result, conclusion |
| `docs/log.md` | session journal, in order |
| `STATUS.md` | current state; leads with the wind-down |
| `PROCESS.md` | the working loop, evidence standards, and unit sizing this ran on |
| `runs/` | logs and candidate paths from every search. Layer directories were deleted at wind-down; every log, input chain and path file was kept |

The evidence discipline is the part worth copying: **facts carry their verification method**,
**"refuted" requires a proof artifact**, and *"nobody has done it"* and *"the community believes"* are
never evidence.

---

## Running anything

You supply your own ROM at `roms/Super Mario Bros. (W) [!].nes`. **No ROM is included and none is in
this repository's history.** `tools/build_core.sh` builds the cores and generates the untracked
`data/xpos_table_11.txt`. Search launchers live in `runs/*/launch*.sh` — every one is committed and
re-runnable. The model searches need the modified engine below.

## The engine modifications

Published separately at **[mrwatts88/smb-opt-modes](https://github.com/mrwatts88/smb-opt-modes)**: a
5,921-line patch against [MrWint/smb-opt](https://github.com/MrWint/smb-opt) adding enemy models
(difftested to 0 diffs), a 4-2 case, two admissible heuristics, and a bucketed diversity beam.

## Third-party content

`data/disasm/smbdis.asm` is doppelganger's SMB disassembly and
`data/wr/happylee-supermariobros,warped.fm2` is HappyLee's TAS movie from TASVideos. Both are included
as research inputs and remain their authors' work.
