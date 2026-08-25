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
