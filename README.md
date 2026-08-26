# smb1-tas

A research project that tried to beat HappyLee's 2011 "warps" TAS of *Super Mario Bros.*
(TASVideos [#1715M](https://tasvideos.org/1715M), **17,868 frames**) using exhaustive and
novelty search rather than hand-optimisation.

**It did not succeed.** The record stands. This repository is the complete record of the attempt —
kept public because the negative results are specific and reusable, and because a few of the tools
and lessons generalise well beyond this game.

## What's here

| file | what |
|---|---|
| **`docs/open-threads.md`** | **start here** — every thread, each closed / dry / parked with a fact number and an artifact. The live board is empty. |
| `docs/facts.md` | the fact ledger, F1–F286. Each is marked **V** (verified by us, with the script or experiment) or **S** (sourced from the community, treated as a claim to verify) |
| `docs/hypotheses.md` | the ideas ledger. Nothing is marked *refuted* without a proof artifact — a search record or a code-level argument |
| `docs/experiments/` | one write-up per experiment: setup, exact command, result, conclusion |
| `docs/log.md` | the session journal, in order |
| `STATUS.md` | current state; leads with the wind-down |
| `PROCESS.md` | the working loop the project ran on |
| `runs/` | logs and path files from every search (~522 logs). Layer dirs were deleted at wind-down; every log, input chain and candidate path was kept |

## What the attempt actually established

The route loses **290 frames to geometry** (the whole budget a movement-based improvement could
draw on). Every priced target inside it was searched where it was priced:

- **1-2** — closed by **arithmetic**, not by a dry search: the level's ceiling is **3** frames against
  a requirement of **8**. An exhaustive rung puts the wall clip at 3, and Maru370's hand-made "perfect
  1-2" independently lands on the same 3. Everything else in the level was verified optimal.
- **8-2** — the largest priced site (114 frames). Two 6-hour archives, **~903M frames**, finished one
  frame *worse* than the WR.
- **8-4's exit pipe** — **~382M frames**, 291 pipe entries, none earlier than the WR's.
- **8-4 novelty sweep** — all five sub-areas, two independent seeds each, **~3.25 billion frames**,
  with an object-slot lens no earlier sweep carried. The 857-frame class it was built to find never
  appeared, and the two seeds **converged bit-for-bit** on the same anomaly inventory.

**What is explicitly *not* claimed: that the record is unbeatable.** One hypothesis class — an
over-cap forward displacement mechanism, priced at up to ~50 frames — has exactly one known instance
and it is clamped away. That is **un-enumerated, not refuted**, and `STATUS.md` says so at the top.

## Things here that generalise

- **A search key that cannot represent its answer fails *silently*.** Two independent negatives were
  produced by a beam keyed on five fields, when the quantity being searched for depended on six.
  Widening the search does not help; the run terminates normally and reports a clean dry.
- **A proxy goal manufactures fake records — and can suppress real ones.** A pipe-entry goal that was
  not position-qualified fired on a *loop-back* pipe 112 frames "early". Because the search only
  records goals that improve on the incumbent, that single false hit made every genuine candidate
  permanently unreportable, while the run kept printing healthy progress.
- **Two launchers for one job drift, and the failure is silent under-delivery, never an error.**
  Happened twice in one day: a 25% under-sized default, then an ignored `SKIP` that spent two machine
  slots on byte-identical duplicate work.
- **Prose is not a queue.** Work described in a document but never entered into the queue the process
  actually reads does not get done.

## Running anything

You supply your own ROM at `roms/Super Mario Bros. (W) [!].nes` — **no ROM is included, and none is in
this repository's history.** `tools/build_core.sh` builds the cores and generates the untracked
`data/xpos_table_11.txt`. Search launchers live in `runs/*/launch*.sh`; every one is committed and
re-runnable. The engine searches need the modified `smb-opt` below.

## The engine modifications

The `smb-opt` engine work is published separately at
**[mrwatts88/smb-opt-modes](https://github.com/mrwatts88/smb-opt-modes)** — a 5,921-line patch against
[MrWint/smb-opt](https://github.com/MrWint/smb-opt) adding enemy models (difftested to 0 diffs), a 4-2
case, two admissible heuristics, and a bucketed diversity beam.

## Third-party content

`data/disasm/smbdis.asm` is doppelganger's SMB disassembly, and
`data/wr/happylee-supermariobros,warped.fm2` is HappyLee's TAS movie from TASVideos. Both are included
as research inputs and remain their authors' work.
