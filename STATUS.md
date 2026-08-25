# STATUS — SMB1 TAS project

This file is the current state only. The story is in `docs/log.md` (one entry per session)
and `docs/experiments/`; standing search rules are in `docs/search-runbook.md`; the
pre-cleanup narrative version of this file is archived at
`docs/archive/STATUS-2026-08-24-pre-cleanup.md`. Keep every section here short.

**Updated:** 2026-08-25 (session 18 — PRIORITY REBUILT: `docs/strategy-review.md` is the official way forward; Track E "the finder" replaces the exhaustive-ladder programme; no search running)

## Where we are
- **READ `docs/strategy-review.md` FIRST (2026-08-25).** It is the official way forward: the
  bottleneck is the state space not the bound, proof is no longer a deliverable, and the plan is
  Track E ("the finder") — an archive-based stochastic search on the real QuickNES core.
- **Target:** beat 17,868 frames (HappyLee, TASVideos #1715M). A new movie must finish with an
  earlier last input than frame 17848 (0-based); framerule = 21 frames (F27–F29).
- **Our best full movie:** none yet.
- **!! SESSION 16 — F122 IS REFUTED AND THE 4-2 TOP ROUTE IS REOPENED (F127/F128/F129).** The
  "top route cannot mint scroll offset" verdict was an artifact of the search method, not the game.
  `--beam N` (lowest-h) and `--beam-offset` are *global single-key* orders = **per-layer
  first-arrival gates**, so any maneuver that pays before it gains dies on the layers it must
  survive (H39/F128). A **bucketed beam** (best N per scroll-offset x y-band x x-speed x subpixel)
  on F122's *own* root and deadline carries the offset **112 -> 132** and reaches a real,
  **core-verified pipe entry** (87/87 frames, 0 mismatches; x 1348 / ScreenLeft 1216 / AreaPointer
  $2F — byte-identical to the WR's entry). The minting maneuver is **19 frames of held Left**,
  which every earlier beam deleted on its first frame. Two of F122's five table rows had never
  measured the offset at all. **It still warps WRONG (F129):** the sct-freeze mint is *transient* —
  the scroll catches up during the descent, crosses 1217 two frames in, destination flips $2F ->
  $42. **The warp needs `Player_X_Scroll` = 0 at entry, a second condition the case never
  modelled** => the engine's `goal_refused` is under-constrained and **every wrong-warp GOAL it
  reports is suspect**. Open question is now cost, not feasibility. `P2.3c-8-beam-diversity.md`.
- **Headline result:** 4-2 main area in **553** frames (movement) vs the WR's 588 — model +
  QuickNES-verified, every segment at its movement bound (F118). **Not a record. The top-route
  claim below is SUPERSEDED by F127 above — read it first (F122, session 14):** the wrong warp needs +20 px of collision-minted
  scroll offset (F40/F120), and the top route **cannot mint it** — minting is the bottom route's
  col-30 floor wall walk; the top route can't reach floor past pipe A (F117) and its offset stays
  frozen at 112 across 5 beam+exhaustive searches. Strong evidence (not formal proof) the top-
  route warp is structurally infeasible — not "2 frames short." **This retires the P2.3c-5 cloud
  fork** (no billion-state proof needed). The 553 stands as a movement result only.
- **And the bottom route is closed too (F123, session 14 cont.):** `--goal-offset` measured the
  mint directly — min 132-mint = 27 frames but every minted state has ~0 speed (the mint
  mechanisms price it in speed; the WR sprints inside the sct-frozen scroll window and is already
  optimal-ish); continuation probe from the chained mint: **total ≥ 584 > 575**. Bottom-route
  floor ≈ 584–585 = deficit ~9–10. **4-2 = 553 movement + ~31 warp-key tax + ~4 slack, conserved
  across routes — closed for a framerule both ways** (residual: H38, a speed-preserving mint).
  **CAVEAT (session 16):** this closure is no longer safe. F123's 27-frame minimum mint came from a
  **single-key** 2M offset-first beam (`mint_cost_beam.log`) — the exact defect F128 documents — so
  it is an upper bound that may be loose the same way F122's was. 4-2 is **not** closed; re-run the
  mint-economics probe with `--beam-buckets` before relying on 584-585.
- **1-1 is now closed END TO END (session 15, F124):** the enemy-aware room-1 rung `bfscx W11Room1E
  … 0 367 --enemies 0` is **dry in 4.7 s** (root bound exactly 367, frontier extinct at layer 21) and
  the bound is provably admissible with enemies — `w11enemies.rs` never touches `x_pos`/`x_spd` (its
  only player write is the stomp bounce), and the case bound is the x table to `0x39400`, the exact
  x the pipe's right-foot `cv 0x11` check demands. **H29 refuted; with H28 (F116) that also closes
  H21** — 1-1 cannot deliver its 1 missing frame on any modeled route. The one unavoidable frame is
  spent on an airborne frame of the opening jump (`k+h` 367 → 368 at step 21, then constant). 4-2's
  warp zone: enemy-free bound 461 vs WR 476 (F89–F91, H35 open).
- **Fork RETIRED; 4-2 closed BOTH routes (F122 top / F123 bottom):** no cloud proof needed. The
  user's cheaper/earlier-mint ideas were tested directly (`--goal-offset`): mint is speed-priced
  at ~30 frames on any route (H38 records the one 4-2 residual).
- **Next unit: P2.2a — the 8-4 turnaround room (H25), already In progress with a checkpoint.** Its
  next step is the `w84enemies` port (piranha plants + the flying-cheep frenzy) → difftest → the
  d194 rung. 1-1, 4-2 are closed; 8-4 is the primary track (decisions.md, session 14 evening).
- **Phase:** P2 (proof engine on the route). ROM verified byte-identical to TASVideos' (W) [!]
  (`tools/verify_rom.py`; copy in `roms/`, gitignored). Host: Linux box primary, Mac overflow
  (PROCESS §"Parallel work on the second host"); emulators in the toolbox container `smb1`
  (`tools/{fceux,mesen2,bizhawk}_run.sh`). Git: private GitHub remote; document → STATUS →
  commit → push after every unit.

## Running jobs
- **[TRACK B, session 17] No Track B job running** — both P3.2 band-A sweeps **finished** (8-4: 61,440 runs / 16.9M frames / 1213 s; 1-2: 61,440 / 23.1M / 1552 s). **Zero earlier endings in either.** Verdict + histograms in `docs/experiments/P3.2-ram-oracle.md` §10, results kept at `runs/P3.2/*.csv`. Relaunch shape: `tools/ram_oracle_sweep.sh TAG AT LO HI`.
- **[TRACK A] No Track A job running** (`pgrep -x smb-opt` empty; 145G free, every layer dir deleted).
  The coin-fixed clip + carry both finished and reproduced their pre-fix results exactly — and **the core
  still rejects the candidate** (F148). See "In progress" for what that means and what comes next.
- **None** (2026-08-24 session 16: the P2.3c-8 rungs all finished on their own; `pgrep -x smb-opt` empty.
  Kept for repicks: `runs/P2.3c-8/mint_d90_layers` 9.1G + `f122_retest_layers` 858M — needed to census a
  ZERO-SCROLL goal parent once F129's goal fix lands; delete after that. 147G free.) Session 15 note: the P2.5b-1 `w11_d368` control was stopped as infeasible —
  see Done/F124 — and its 94 GB layer dir deleted; `pgrep -x smb-opt` empty; 147G free). Beam-tooling
  lesson recorded: layer dirs MUST live on the NVMe (`/home`), never the tmpfs scratchpad (`/tmp`,
  7.7G RAM-backed) — a run filling tmpfs OOM/quota-dies AND starves the shell of fork memory.
- **Sizing lesson (session 15):** a `--check-path` rung at deadline = optimum+1 is NOT a cheap
  control — zero slack gives tens of states, one frame of slack gives tens of millions (the bound is
  a coarse x-only table). The control you actually want runs *before* layer 1: `--check-path N`
  audits the reference path's bound and goal at startup (main.rs:938–950). Read that, then decide
  whether the exhaustive part is worth its disk.
- Standing rule: **never start a search without a cgroup cap** — not even a short control
  (`docs/search-runbook.md` §1). Check here first every session; list each job with machine,
  pids, log path and how to read the verdict.

## In progress
- **E1 + E2 — declared 2026-08-25 session 18 (Track E, `docs/strategy-review.md`).**
  E1 = the free-knob check (is level-entry state a pure function of the entry frame?).
  E2 = the last-input reformulation of 8-4 (earliest frame after which the null-input continuation
  still reaches the axe). Both are small and both are read/replay work on artifacts that already
  exist (`data/wr/fceux_wr.ram`, `build/harness`). Acceptance in the Next-up table.
  Write-up: `docs/experiments/P4E-finder.md`.
- **P3.2 — RAM oracle (Track B) — declared 2026-08-24 session 17. THIS IS A SECOND, PARALLEL SESSION.**
  Goal: per-level single-byte perturbation sweep on the QuickNES fast core -> the "jackpot cell" map
  (which `(address, value)` writes make the game end earlier), which turns P3.3's write-reachability
  hunt from a fishing trip into a targeted one. Acceptance: `docs/experiments/P3.2-ram-oracle.md`
  with the cell list; H7 status updated.
  **PARALLEL-SESSION PROTOCOL (another session is working P2.2f in this same working tree):**
  Track B needs **no engine sharing** — it runs on the QuickNES fast core (`src/fastcore/`,
  `build/harness`, `third_party/QuickNES_Core`), not on `third_party/smb-opt`. It touches ONLY new
  files: `src/fastcore/ram_oracle.c`, `tools/ram_oracle*`, `docs/experiments/P3.2-ram-oracle.md`,
  `runs/P3.2/`. It never edits `third_party/smb-opt`, `tools/smb-opt-modes.patch`,
  `tools/build_core.sh`, or any `w*.rs`. Both sessions must commit with **explicit pathspecs —
  never `git add -A`** — and edit STATUS/log/facts **in place, never rewrite the file**.
  **Fact numbers are split to avoid collisions: Track A keeps F135+, Track B reserves F200+.**
  Resource discipline: Track B caps itself at 4 of 12 threads under `systemd-run MemoryMax` and
  checks "Running jobs" before launching anything (the box has ~9 GB available and swap is full).
  **CHECKPOINT (session 17): the oracle is BUILT, all four controls PASS, and band A is running.**
  `src/fastcore/ram_oracle.c` + `tools/build_oracle.sh` -> `build/ram_oracle`. Controls: null poke
  -> `CONVERGED(noop)` at frame 0; positive poke (`$0770` = 2) -> `VICTORY` 2,808 frames early;
  14,949 fps (= F46's 15.0k); core victory frame 17864 = dump 17867 - 3, re-deriving F45's origin.
  Success predicate = first `OperMode` ($0770) == 2 earlier than the baseline's core frame 17864 (**F200**).
  **Two route-level findings already (F201, F202):** F43(a) has no target on the warp route (exactly
  one castle, 8-4, where WorldNumber is already 7; 255/256 values there just kill the run), and the
  real prize $06D6 (WarpZoneControl in 1-2 -> 8-1, skipping 4-1/4-2) sits **7 bytes above** the only
  proven OOB writer's `$06CF` ceiling — so **H7(c) is narrowed, not refuted**, to "is P3.1's $06CF
  reach bound tight?".
  **NEXT:** read the two band-A sweeps; then band B (`$0700-$07FF`) at every level entry; re-run any
  live-looking band with `--no-death-exit` (the DEAD early exit is a stated assumption, not a
  theorem — `P3.2-ram-oracle.md` §2); then the ranked cell list -> P3.3 + the $06CF question.
  **CHECKPOINT 2 (session 17) — band A is DONE and the unit has turned over. Three results:**
  **(1) F203 — the $06CF question is ANSWERED: the bound is tight.** Code-level proof ($07 always $05
  because the 2-entry `BlockBufferAddr` table's nybble index is bounded to {0,1} at both call sites;
  $06 <= $DF; y <= $F0). So `$06D6` WarpZoneControl misses the only OOB writer by **7 bytes** and
  `$075F` WorldNumber by **144** — H7(b)/(c) closed *for this mechanism*, H7 itself still open on
  P3.1 §4's three unaudited write classes.
  **(2) F205 — band A is negative but sharply localized.** 122,880 runs, **zero earlier endings**;
  238 of the 240 addresses are completely inert (the renderer rewrites the band). **Every**
  non-converging row in both levels is at `$06CB`/`$06CD` = `EnemyFrenzyBuffer`/`EnemyFrenzyQueue`.
  Caveat: the sweep pokes ONE frame per level, which undersamples exactly those cells.
  **(3) F206 / H43 — a complete cart-swap-free ACE chain, and its target is INSIDE the writable window.**
  `CheckFrenzyBuffer` copies $06CB into `Enemy_ID` unchecked; both enemy JumpEngines (55-entry init,
  34-entry run) accept indices far past their tables, so `jmp ($06)` takes PC from post-table bytes;
  and $06CB is `$05D0 + col 11 + y $F0` — exactly the "odd-page column 11/12 writer above Y $20"
  `oob-audit.md` §5 left open after H30. **This is the first H7-class target that is not out of reach.**
  **NEXT (in priority order): (a) H43(a)** — enumerate which *metatile values* the block-buffer writers
  can actually place into $06CB and what each is as an `Enemy_ID` (pure disassembly + `tools/area_data.py`,
  no CPU); **(b) H43(b)** — hunt a writer reaching odd-page column 11 above Y $20 (`HandleEToBGCollision`,
  `ErACM`, `PutMTileB`); **(c)** a **temporal** sweep of $06CB/$06CD across many frames per level, which is
  the test band A could not perform; **(d)** band B (`$0700-$07FF`) at every level entry.
  **CHECKPOINT 3 (session 17) — H43(a) ENUMERATED, and the trigger is identified (F207). The chain is
  complete at code level and the jump is empirically confirmed firing.**
  The enumeration answered the question that decided it: the OOB-capable block-buffer writers place
  `$26` (vine — and the vine is *explicitly* guarded `cpy #$d0 / bcs ExitVH`, so it can never write OOB
  at all: stronger than H30), `$23`, `$00` (x3, inert), and — the one that matters — **`Block_Metatile`**,
  whose reachable values include **`$c4`** (empty block), **`$58`/`$5d`** (coin bricks) and, for small Mario,
  the bumped metatile itself. As `Enemy_ID`s those are **196 / 88 / 93**, all far past the 55-entry table.
  **The trigger is `PlayerHeadCollision`**: bumping a block latches the *wrapped* address
  (`lda $02 / sta Block_Orig_YPos,x`, `lda $06 / sta Block_BBuf_Low,x`) into the block object, and
  `BlockObjMT_Updater` writes `Block_Metatile` there on a later frame. Odd-page **column 11** + y `$F0`
  = **$06CB** exactly.
  **Empirical support:** of the live rows at $06CB, **137/146 (8-4) and 125/128 (1-2) have value >= $37** —
  the out-of-table indices are the ones that do anything. `$c4`/`$58` die in ~165 frames after visiting a
  non-baseline `AreaPointer`; `$5d` diverges for the ENTIRE remaining movie (15,922 frames at 1-2).
  **NOT yet an exploit** — the sweep *poked* the cell rather than reaching it via a bump; no jump
  destination has been computed; no route position with a bump at Y+adder < $20 on odd-page col 11 exists yet.
  **NEXT, in order: (1)** compute where index `$c4` actually lands (locate the init table in the ROM, read the
  27-28-bytes-past pointer) — decides steerable-vs-crash; **(2)** search for a route position allowing a head
  bump above the status bar at odd-page column 11 (this is a geometry/physics question — exactly what the
  Track A search engine does, so it is the first place the two tracks would MERGE); **(3)** a temporal sweep
  of $06CB/$06CD across many frames; **(4)** band B.
  **CHECKPOINT 4 (session 17) — THE JUMP IS OBSERVED, AND IT IS STEERABLE-ISH (F208).** `--probe` mode added
  to `ram_oracle` (per-frame trace of $06CB/$06CD/`Enemy_ID`/`Enemy_Flag`). Poking `$06CB = $c4`: the value lands
  in **enemy slot 1's `Enemy_ID` 163 frames later** (`CheckFrenzyBuffer`'s next run — which is exactly why the
  single-frame band-A sweep undersampled this cell), and **two frames after that `OperMode` goes 1 -> 0 and
  `WorldNumber` 7 -> 0**: the jump reaches a real reset path, not garbage. **Label correction: `DEAD` on $06CB rows
  means "run terminated", NOT "Mario died"** — the game resets and the reinitialised lives byte trips the detector.
  **The destination is a function of the BYTE, not the level:** all 128 of 1-2's live values are live in 8-4 too, and
  **123/128 shared values give the same outcome class in both levels** — the signature of a fixed jump-table index.
  **And the primitive reaches area-loading code**: different values visit `AreaPointer` values absent from baseline
  ($00/$02/$1f/$e5 in 8-4; $00/$c0 in 1-2) — i.e. it can touch **$0750/$0751, which is F43(b)**, an H7 target
  previously judged unreachable. No value yet produces an earlier ending or a higher `WorldNumber`.
  **NEXT: (1)** classify all ~137 out-of-table values by what they actually DO (probe each, record OperMode/
  WorldNumber/AreaPointer trajectory) — this is the steering map, and it is cheap; **(2)** hunt specifically for a
  value that sets `AreaPointer`/`EntrancePage` to $65/16 (F43(b) = Bowser room from any down-pipe) or WorldNumber >= 7;
  **(3)** the temporal sweep (the +163-frame delay proves timing matters); **(4)** then the physical trigger
  (head bump above the status bar at odd-page col 11) — the Track A merge point.
  **CHECKPOINT 5 (session 17) — STEERING MAP BUILT (F209) AND THE ENTRANCE IS FULLY SPECIFIED (F210).**
  **Steering map** (512 runs, `$06CB` x 256 values, `--no-death-exit`, both levels): ~6 reproducible classes —
  110 no-effect / 89 in-level divergence / **49 that load areas absent from baseline (`AreaPointer` $00/$25/$c2)** /
  4 game-over (values 20, 84, 148, 212) / 2 victory-at-baseline-frame (46, 174). The $00/$25/$c2 class fires for the
  **same values in both levels**, confirming F208. **ZERO earlier endings in 512 runs.** (1-2 values 21/149 showing
  world 7 + area $65 are a FALSE LEAD — `frames_run` 15799 = they re-converged at 17742, so that is the normal route.)
  **Entrance (F210) — it is NOT "above the status bar", it is ABOVE THE TOP OF THE SCREEN.** `HeadChk`'s guard
  `cmp PlayerBGUpperExtent,x` with `.db $20,$10` and `ldx PlayerSize` means **small Mario** (our route) needs only
  `Y >= $10`; the small-Mario head adder is `BlockBuffer_Y_Adder[$0e]` = **$12 = 18**; solving `((Y+18)&$F0)-$20 = $F0`
  with the guard leaves **`Player_Y_Position` in {$FE, $FF} — a 2-pixel window**, i.e. the coordinate wrapped, Mario
  above the screen top. Plus: **Y-speed negative** (still rising), `Y & $0F >= 4` (both values pass), **odd page,
  column 11**, `AreaType` != water, `BlockBounceTimer` expired, and the byte already in $06CB must be **nonzero,
  non-coin, non-solid** (the OOB read and write are the SAME cell).
  **NEXT: (1)** temporal sweep — poke $06CB/$06CD at many frames per level, not just entry (F208's +163-frame delay
  proves the single-instant sweep is the weak test, and F209's null is only about that instant); **(2)** the same
  sweep on **$06CD** `EnemyFrenzyQueue`, never yet swept alone; **(3)** hand the F210 predicate to the Track A engine
  as a search goal (small Mario, Y in {$FE,$FF}, y-speed < 0, odd page col 11) — **this is the Track A/Track B merge
  point** and 4-2's top route already puts Mario at the screen top; **(4)** band B (`$0700-$07FF`).
  **CHECKPOINT 6 (session 17) — PRIORITIES RESET BY THE USER: characterise the primitive first
  (when can it fire / where does it go / is it real), NOT score it against the record. Two big answers.**
  **(A) F211 — the trigger is ALREADY on the WR route, twice.** Dump scan for F210's conditions: Mario hits
  `Y in {$FE,$FF}` while **rising** on an **odd page** as **small Mario** at **frame 5369 (4-1, column 8)** and
  **frame 10291 (8-1, column 0)**. Required column is **11**. So the open question is not reachability — it is
  shifting x by a few columns at a moment the route already visits. That is a Track A search problem.
  **(B) F212 — the destination map is computed.** Tables located: `InitEnemyRoutines` at CPU **`$c282`** (55
  entries), `RunEnemyObjectsCore` at **`$c892`** (34). `JumpEngine`'s `asl` drops the carry so offset =
  `(2*index) mod 256` and **index aliases with index+128** — confirmed from black-box data, since every
  behaviour pair in F209 differs by exactly 128 (20/148, 46/174, 116/244). **63 out-of-table destinations,
  three classes:** unmapped/open-bus (**these are the resets** — `$c4`->`$60cf`), real PRG ROM (id 93->`$a9c3`,
  id 116->`$a960` — diverge without dying), and **zero-page RAM: ids 83/96/211/224 -> `$00a9`**. The RAM target
  is only weakly controllable (`$a9`-`$b3` are sprite high-position bytes, ~5 distinct values, mostly `$00`=BRK
  and `$02`=JAM as opcodes).
  **REVISED NEXT, in the user's order — characterise, don't score:**
  **(1)** Probe ids **83 and 96** specifically (the RAM jump) and trace what executing `$00a9` actually does.
  **(2)** Enumerate what can WRITE `$a9`-`$b3` — if a payload can be staged there, class (c) is real ACE;
  if those bytes are structurally limited to {0,1,2,254,255}, say so and pivot to class (b).
  **(3)** For class (b), work out which PRG entry points do something useful (the 63-target list is small
  enough to read by hand against the disassembly).
  **(4)** Prove it END TO END through a real head bump rather than a poke — the F210 predicate handed to the
  Track A engine as a search goal from the F211 states (4-1 frame 5369 / 8-1 frame 10291).
  **(5)** Only then go back to timing sweeps and record-scoring.
  **Predicate fixes shipped this session** (`ram_oracle`): route-progress vs the WR itinerary, an OperMode==1
  gate (the raw version produced a FALSE POSITIVE — $06CB=116 in 1-2 read as "334 frames ahead" but the probe
  shows it was a transient `AreaPointer` during the reset), route-agnostic `world_ahead`, and **`novel_world`**
  for worlds the WR never visits at all (H44 — `world_ahead` scored those ZERO by construction, since there is
  no baseline frame to beat; a world the WR never enters may still lead somewhere better via an unknown warp).
  **CHECKPOINT 7 (session 17) — THE LINE IS BLOCKED, AND WE KNOW EXACTLY WHERE (F215). Unit conclusion.**
  Chased the one question that decided it: **can a real head bump plant a useful byte?** No.
  `BlockBumpedChk` does not modify A, so for **small Mario with no table match the deferred write is a COPY of
  the byte already there**; a match writes **`$c4`**; big Mario writes **`$00`**; the immediate write is always
  **`$23`**; every other OOB-capable writer writes `$00`; and the vine is explicitly guarded out of OOB entirely.
  So the complete mintable set is **{`$00`, `$23`, `$c4`, copy}**. As `Enemy_ID`s: `$00` inert, **`$23` is
  IN-TABLE for both dispatches** (jumps nowhere), and **`$c4` is the only OOB value — its init dispatch goes to
  `$60cf`, unmapped, which is precisely the reset F208 observed.** The five RAM-executing IDs (59/132/133/140/187)
  are **not mintable by any known writer**, so the self-hosting `$06B5` idea is dead as designed. `$c4` at `$06CB`
  is doubly blocked: minting it needs that cell to already hold a brick metatile, and `EnemyFrenzyBuffer` only
  ever receives small enemy IDs.
  **What this does NOT close:** P3.1 §4's three unaudited writer classes — stack overflow/underflow, non-indexed
  writes, `VRAM_Buffer` writes indexed by `VRAM_Buffer1_Offset`. That is now H43's *only* opening, and it is a
  bounded reading job, not an open-ended hunt.
  **What SURVIVES as durable value from this unit** (all V-grade, all committed):
  F200 ending predicate; F201/F202 H7 targets narrowed; **F203 the $06CF reach bound is tight**; F205 band A
  inert except the frenzy pair; F206-F208 the JumpEngine OOB is real and observed firing, destination is
  value-determined; F209 the steering map; **F210/F211/F214 the trigger geometry is fully specified and the WR
  route already enters it 8 times across 4 levels**; F212/F213 the destination map (two tables, 128 aliased
  indices, 3 destination classes, 5 RAM-executing IDs); F215 the value-minting block.
  Tooling: `build/ram_oracle` with `--probe`, route-progress, OperMode gate, `world_ahead`, `novel_world`.
  **NEXT UNIT (Track B): P3.3 — audit the three remaining writer classes.** If any can write an arbitrary byte
  into `$05E0-$06CF`, every other piece of this chain is already built and mapped, and H43 reopens immediately.
  If none can, H43 is refutable with a proof artifact for the first time. Either way it is a bounded disassembly
  job with a clear verdict, and it needs no CPU.
  **CHECKPOINT 8 (session 17) — P3.3 DONE: all three previously-unaudited writer classes audited. None
  yields an arbitrary write, so H7/H43 have no known opening left.**
  **(1) Non-indexed writes (F220) — adds nothing.** Every store to the four H7 cells is a legitimate
  transition already modelled by P0.6. `WorldNumber` in particular has exactly two writers in the whole ROM:
  `GoContinue` (1056) and the `inc` in `PlayerEndWorld` (1241). Nothing sets it to an arbitrary value.
  **(2) Stack (F219) — closed to redirection.** Exactly ONE `txs` in the ROM (line 680, power-on init) and
  **no `tsx` anywhere**: the stack pointer is set once and never read back, so no input relocates it.
  Residual named: no static call-graph depth / pha-pla balance analysis.
  **(3) VRAM_Buffer overflow (F218 + F221) — the live one, now bounded.** `VRAM_Buffer1` is 64 bytes at
  `$0301` but the store is 8-bit indexed, so the reach is `$0301-$0400`, which contains **`Block_Orig_YPos`
  `$03e4` / `Block_BBuf_Low` `$03e6`** — corrupting those would make the deferred block write land anywhere in
  `$0500-$06FE`, **including `$06D6` WarpZoneControl**. `SetVRAMOffset` has NO clamp. What bounds it: the offset
  is reset every NMI by `InitBuffer` (indexed by a 2-entry table, x ∈ {$00,$40}); the amplifier is `MoveVOffset`
  (+10 per block-metatile write) whose only callers are **one head bump per frame**, **`BlockObjMT_Updater`
  (self-gated: `lda VRAM_Buffer1 / bne NextBUpd` skips when the buffer is in use)** and **bridge collapse (one
  tile/frame)**; enemies write the block buffer directly (`HandleEToBGCollision`) and never advance the offset;
  `RemoveCoin_Axe` targets buffer 2. Enumerated ceiling ~40-70, **observed max 67 over 18,268 WR frames**,
  needed **227**. Narrowed to a small specific residual, **not formally refuted**.
  **NEXT (Track B):** the only remaining moves are (a) machine-check F221's per-frame sum to make the VRAM class
  **CHECKPOINT 9 (session 17) — P3.2/P3.3 CLOSED ON CAPABILITY, NOT ON PROOF (F222). Unit done.**
  User's steer: stop chasing proof-grade closure of a dead end and test whether anything WORKS. Right call, and
  it also killed the queued temporal sweep — sweeping `$06CB` tests a capability F215 shows we do not have.
  **The right experiment was the inversion:** sweep only what a real head bump can actually do — values
  **{`$00`,`$23`,`$c4`}** into the genuinely reachable cells (`$06A0`-`$06CF` odd page, `$05D0`-`$05FF` even page).
  That is the COMPLETE action space of the only OOB write primitive in the game: **430 runs**, at 1-2 and 4-1,
  scored on earlier-victory + OperMode-gated route-progress + `world_ahead` + `novel_world`.
  **Result: ZERO hits on every predicate. `max_opermode` never exceeded 1 in any run.** Overwhelmingly
  `CONVERGED` (absorbed), plus 128 `CONVERGED(noop)` null-control rows passing.
  **So Track B's ACE/OOB line is exhausted at the capability level** — not "we didn't find a jackpot" but "the
  primitive's whole reachable behaviour is enumerated and none of it helps". Not claimed: that SMB1 has no
  exploit at all. Untested dimension: timing (F205's single-instant caveat).
  **NEXT: return the effort to Track A, where frames actually come from.** Queue head per this file's Next-up
  table: **P2.3c-9 Part B** (the 4-2 top-route warp-cost ladder — "the 4-2 hope" thread says the cheapest mint
  has never been measured, and that measurement IS the decision) and **P2.2a'** (8-4 room-3 multi-apex seam).
  Track B keeps its PROCESS-mandated slot but has no live lead; revisit only if a new writer class appears.
- **P2.3e — THE PRIORITY REVIEW SAYS THIS IS THE UNIT (declared 2026-08-24 session 17, after the user
  challenged the whole allocation — and was right).** Goal: a feasibility scan of **1-2, 4-1 and 8-3**,
  then the full pipeline on the cheapest, starting with **1-2**.
  **The argument, in numbers, from this file's own Key numbers table.** Deficits (frames needed to bank a
  21-frame framerule): **1-2 = 5** on Maru's route (8 on the WR's), **8-3 = 7** with FPG+242 (10 without),
  **4-1 = 9**; versus 1-1 = 1 (CLOSED, proof-grade) and 4-2 = 10-13 (CLOSED both routes). And the coverage
  line: *"WR vs MrWint segment optima: gap 0 on all 10 solved segments (1-1 x4, **1-2 opening**, 8-4 x5)"*
  — so **4-1, 8-3, 8-1, 8-2 and all of 1-2 past its opening have NEVER been exhaustively searched by
  anyone**, MrWint included. Confirmed in his sources: `w12.rs` ships only `W12Speedup` (the 71-frame
  opening), `W12Powerup` (mushroom, warpless route) and `W12Flag` (half-flagpole) — **nothing covering
  1-2's body to the WARP ZONE, which is the warps route.**
  **Why the prior is good, not hopeful.** The one time this pipeline was pointed at a route nobody had
  optimized (4-2's top route) it found **35 frames** of movement (553 vs the WR's 588). That only failed
  because 4-2's wrong warp charges a ~31-frame key tax (F123). **1-2, 4-1 and 8-3 have no such tax** — a
  frame found is a frame banked toward the deficit.
  **Contrast with what we were doing:** 8-4 and 4-2 are the two most pre-optimized levels on the route.
  8-4's segments are MrWint's own solved set; F139 just re-confirmed one of his seams does not leak.
  **Acceptance:** a scan table in a new experiment file (block map via `tools/blockmap_from_dump.py`,
  enemies via `tools/area_data.py`, model gaps, which segments are RNG-free, warp-zone entry condition)
  with the chosen level and why; then a case exact on the WR's frames and a first segment bound vs the WR.
  **Order:** 1-2 first (cheapest deficit AND unsearched) — **DONE, F145**. Then 8-3 vs 4-1 is decided by a
  **code-level cost comparison of the Hammer Bro ($05) against Lakitu ($11)+Spiny ($12)**, not a guess:
  scanning the WR's own enemy slots showed **4-1 is NOT blocker-free** (an earlier claim here, corrected) —
  both remaining candidates carry an RNG-coupled object. 8-3 leads on deficit (7 vs 9) and needs no new
  block map; 4-1's map is already extracted (`BB41`, committed). F130 is the precedent for pricing the RNG
  at code level before assuming it is expensive.
  **DONE s17 (F140/F141/F142) — `W12Warp` IS EXACT ON ALL 1280 FRAMES, AND THE WR's LAST 60 ARE PROVED OPTIMAL.**
  • Span: fceux row **2486** (the GES 7 -> 8 handoff; NOT 2469 — that handoff **duplicates a frame**) ->
    row **3766**, the world-4 warp pipe. **1280 frames, one piece, no room seam.** Map `BB12W` = MrWint's
    `BB12` + the dump's cols 192..199 (the warp zone he never covered).
  • Goal: `EnterVerticalPipe<U178, U8>` AND `screen_left_abs >= 2816` — the F40-shaped condition arming
    `WarpZoneControl = 4`. Bound: `build_overshoot_bound(2928, 2860)`, because the route is a turnaround.
  • **Port finished:** `CLASS_LIFTPLAT` (ids `$26`/`$27`, the `MoveLiftPlatforms` elevators — the same object
    as 4-2's lift, so its collision code was reused) and `CLASS_REDKOOPA` ($03).
  • **Two real engine bugs fell out, one of them live in 4-2 and 8-4 too (F141):** `CheckpointEnemyID`'s
    +8 px applies **only to ids < $15** (platforms/powerups/vines were 8 px too low); and **bounding boxes
    were never clamped at the screen edges**, so two goombas **250 px apart** turned each other around
    (18/150 battery trials). Both fixed.
  • **Validation:** WR **1280/1280 exact** (6 stomps, pipe entry frame-identical); battery **150 trials /
    96,424 frames / 0 differences**; `--check-path 1280` = **GOAL, 0 bound violations**. Every prior
    regression still exact (4-2 gate, 4-2 596-frame chain, 8-4 room 2 at 401 trials / 0 diffs).
  • **F142 — the ladder:** the bound is **TIGHT for the last 46 frames** (from step 1234, the overshoot apex
    at x 2944), which is a proof on its own; then prefix 1230/**d49 DRY** and prefix 1220/**d59 DRY**.
    **The WR's last 60 frames of 1-2 cannot be improved by one frame.** The wall is *terrain*: at 1220 Mario
    is in the narrow warp-zone corridor and the frontier suffocates; at 1210/1200 he is in open ground and
    it explodes (8.9M by layer 14; 101M by layer 25 / 28 GB).
  • **F143 — where 1-2's slack actually is, and a near-miss worth remembering.** The slack profile is flat
    at 54-55 from step 40 to ~1080 (Mario is at the **x-speed cap for essentially the whole level**), then
    collapses **54 -> 23 between steps 1080 and 1120**: the **wall clip**, where the WR spends 40 frames and
    the bound expects 9. A position-goal probe there (`--goal-x 2700 --goal-y 64` from step 1080) reached
    the gate in **33** against the WR's **42** and **core-verified 33/33, 0 mismatches** — and it is worth
    **nothing**: the arrival is `x speed ~0, JUMPING, moving LEFT, sct 15` vs the WR's `speed 21, STANDING`,
    and its continuation is **pruned at layer 1** (>= 47, exactly the WR's cost). **F115/H39 at the finest
    granularity — a first-arrival gate on a scalar is not a seam.** It did prove something: from the WR's
    step-1113 state the next milestone is **dry at d46** and reached at 47, and the WR pays 47, so **the WR
    is optimal on that stretch too**. Method note now in the experiment file: model step k = fceux row
    **2486 + k**; a hand-mapped RAM row briefly turned that tie into a phantom frame.
  • **F147 — THE CORE CAUGHT A SILENT MODEL BUG, AND F144 IS NOW PROVISIONAL.** A searched path core-replayed
    to a **death the model did not have**. `IgnoreCoins` meant collecting a coin never filled `VRAM_Buffer1`,
    a busy buffer **stalls the area parser for a frame**, and the stall moves every piranha-plant spawn after
    it — model f3058 vs core f3059 for the pipe-(103,8) plant, which by the warp zone was **1 px** of plant y
    and exactly the pixel between a valid path and a death. Fixed (`coin_list_handler!` moved to
    `case/mod.rs`; `W12WarpCoins`, 17 cells; key 20 → 22). **Re-verified identical on the fixed model:** WR
    1280/1280, the loss map (66 frames, tight from 1234), F142's rungs (dry at layers 4 and 14), F143's (16),
    and 4-2 + 8-4's regressions. **So F142/F143/F145 stand; F144's three frames are being re-earned.**
  • **F144 (PROVISIONAL, re-running) — three frames in 1-2's wall clip, and the scroll takes them back.** Exhaustive rung from
    the WR's step 1080 to the post-clip milestone: **goal at layer 77 where the WR pays 80**, and the arrival
    **dominates** the WR's (same Y / STANDING / running timer, at the x-speed cap with a better fraction, and
    0.25 px further right). **Core-verified 77/77, 0 mismatches.** The lead survives to step 1217 — the
    60-frame carry is **bound-tight** (h = deadline = 60) and the whole 137-frame segment core-verifies at
    **0 mismatches** — and then **the pipe is DRY at 60**, exactly the cost the WR pays from its own
    step-1220 state. **Mechanism: `ScrollLockObject_Warp` arms `WarpZoneControl = 4` when SCREEN LEFT hits
    its locked maximum 2816 — a property of where Mario has BEEN.** At step 1217 we match the WR's x with far
    more speed (40 vs 22) and height (Y 107 vs 124), but ScreenLeft **2806 vs 2809**. *In 1-2 a frame banked
    before the warp zone is a frame lent to the scroll.* The §3.2 check was run — `offset-census --sl` (new
    flag: rank by absolute ScreenLeft) over layer 59's 639,657 records gives max ScreenLeft **2803**, and our
    auto-pick came through it, so the refund is **not** a pick artifact.
  **WHERE 1-2 STANDS:** last 60 frames optimal (F142); steps 1113-1160 optimal (F143); the WR is x-optimal
  from step 40 to 1080 (h drops by exactly 1 per frame there — see the loss map in P2.3e §12: only **66**
  frames are lost to the bound in the whole level, 11 in the entrance fall, 1 at step 487, 31 at the clip,
  23 at the turnaround). **The 3 clip frames are the only ones found, and the scroll refunds them.**
  **The remaining openings, in order:** (1) one of the **2.0M** goal transitions at clip-layer 77 might reach
  the milestone with a better scroll — a deeper search than has been run; (2) the isolated **1 frame at step
  487** (x 1183, mid-jump over the col-80..82 pit at x speed 38 instead of 40) is cheap to probe and untested;
  (3) 1-2's **intro area** (fceux rows 1946-2443, ~500 frames) is not modelled at all and Maru's 3-frame gain
  over the WR has to be somewhere — this is the only stretch nobody has looked at.
  • **F148 — A RESIDUAL PARSER-ORDERING GAP, AND IT MAKES EVERY 1-2 SEARCH RESULT PROVISIONAL.** With F147
    fixed the searches reproduced exactly (clip layer 78 / 3,180,666; carry layer 60 / 7,879,141) and the
    78-frame clip core-verified 78/78 — **and the core still killed Mario at frame 3690**, same plant, same
    1 px. The pipe-(103,8) plant now spawns f3059 in both, but the **warp-zone pipe-(182,8) plant spawns
    f3566 in the model vs the core's f3567 — on the WR's own path**. Walking `AreaParserTaskNum` against the
    core frame by frame, the first divergence is **step 446 / f2930**, the exact frame `CoinTally` goes
    20 -> 21 (Mario head-bumps the coin at cell (68,6), which IS in the handler).
  **s17: DIAGNOSED AND FIXED — and the ordering hypothesis above was WRONG.** `run_step` already runs the
  player before the parser, exactly as `GameEngine` does. Two real defects, both now fixed and documented in
  `docs/experiments/P2.3e-framerule-scan.md` Part 7:
    - **F149 — `CheckTopOfBlock`.** Mario head-bumps the **brick at (68,7)**; the `$c2` is the coin sitting
      **above** it at (68,6), which `BumpBlock`/`BrickShatter` take via `CheckTopOfBlock` -> `RemoveCoin_Axe`
      (AddrCtrl 6 -> parser stall) -> `SetupJumpCoin`. The model had no such path. Two cells on 1-2's route:
      (60,7) and (68,7). `CoinBlock` (a `$c0` whose *contents* is a coin) writes no AddrCtrl 6 and is
      correctly ignored — that is 4-2's one missing coin, and it costs nothing.
    - **F150 — `ScrollLock`, which 1-2's whole warp zone runs on.** `ScrollLockObject` at **column 178**
      toggles it (a set flag = **no scroll at all** that frame); `WarpZoneObject` ($34) clears it and arms
      `WarpZoneControl`, **but only on a frame where Mario's Y is even**; `ScrollLockObject_Warp` at
      **column 198** arms the warp zone, kills every plant, and **falls through into `ScrollLockObject`**.
      Without it the model's screen-left ran **2 px ahead** for the last 222 frames — up to a phantom frame
      at a goal that was `ScreenLeft >= 2816`. The goal is now the exact `blocks.warp_armed`.
  **Controls, all green (F151, `tools/parser_check.py` — the new per-frame control on `AreaParserTaskNum`,
  `ScreenLeft_X_Pos`, `ScrollLock`, coin metatiles):** 1-2 **1280/1280**, 4-2 **587/587**, 8-4 room 2
  **267/267**; 4-2's `--lift 0` gate byte-identical; 1-2's 400-trial battery **58,984 frames, 0 diffs**.
  **s17 re-run on the corrected model — DONE, and the clip's three frames survived:**
    - clip `2486 1080 79 --goal-x 2784 --goal-y 64` -> **goal at layer 77** (the WR pays 80), 2,868,570 goal
      transitions; path `runs/P2.3e/clip77_f150.bin`, **core-verified 77/77, 0 mismatches**.
    - F142's rungs re-run: prefix 1230 d49 **dry at layer 4**, prefix 1220 d59 **dry at layer 14** — the same
      verdicts as before (root bounds moved because the goal is now `warp_armed`, the conclusions did not).
    - `runs/P2.3e/{clip78b.bin,carry3_60.bin,seg138b.bin}` are the OLD, INVALID templates (pre-F149/F150).
  **RUNNING — the joint two-segment bucketed beam, i.e. §21's named residue run as one piece.** Chaining
  clip -> carry cannot optimise the scroll, because the clip's arrival is picked by a position goal and the
  rest inherits whatever scroll it has. So: steps **1080 -> the pipe in ONE search**, no intermediate goal.
  `bfscx W12Warp data/wr/wr_inputs.bin 2486 1080 199 --enemies 0 --beam 5000 --beam-buckets x,off,y,spd,e
  --beam-max 3000000 --check-path 200`, log `runs/P2.3e/joint_beam_d199b.log`, layers
  `runs/P2.3e/joint_layers`. **Deadline 199 vs the WR's 200, so any goal is at least one frame.** Root bound
  146 (53 slack — far past exhaustive, hence the beam). `--check-path` reports **0 bound violations over the
  WR's 200 steps**. Runbook §7.2: a goal is a candidate to core-verify; no goal proves nothing.
  If it finds one: `bfscx-path` -> `replay_check --down` -> then re-price the level. If it does not, widen
  the beam or bucket on the scroll more aggressively before concluding anything.
  **AFTER that: `P2.2f-bound` — a TWO-level unlock.** 1-2 loses ~22 frames of bound slack over its
  open region and 8-4 room 2 loses 14, for the same reason: **an x-only bound cannot price a turnaround's
  vertical half.** Build the coupled end-game term and both ladders go deeper. After that: re-run 1-2's
  ladder from prefix ~1150 and below, where the remaining 5-8 frames would have to live.
- **P2.2f — PAUSED 2026-08-24 s17 after the priority review below. Port DONE and validated; room 2 has two
  proof-grade verdicts; the one open question is gated behind `P2.2f-bound` (Next up). Do not resume before
  that bound exists.** H42: dissolve MrWint's 8-4 room-2 seams (declared s16).
  Span: the room in ONE piece — control (WR dump row **15918**, fceux RAM index 15917, page 7, x 1848) →
  the clip pipe entry at **(col 152, row 4)**, x 2436. WR = **267** frames, 8-4 is unquantized (H24), so a
  goal at **≤ 266 IS THE RECORD**. Case `W84Room2` in `third_party/smb-opt/src/case/w84.rs`; full write-up
  `docs/experiments/P2.2f-84-room2-seam.md` (Part 2 = this session).
  **DONE this session — the enemy port is finished and validated (F135/F136):**
  • `w42enemies` is now the shared engine, parameterised on area (`edata`/`pipes`) AND terrain
    (`Slots::step::<B>`; `BB42` for 4-2, `BB84` for 8-4). New `CLASS_PARA` = the `$0e` jumping Green
    Paratroopa (`InitJumpGPTroopa` with NO `InitVStf`, `MoveJumpingEnemy` force `$1c` dispatched by ID,
    `EnemyJump` BG collision, `ChkForDemoteKoopa` on a stomp). Class 8 packs as low-bits-000 + byte-0 bit 7,
    so every 4-2 record keeps its bytes.
  • **New stomp rule**: `ChkForPlayerInjury` stomps an id ≥ `$07` object even while Mario RISES, when
    `Player_Y + 12 < Enemy_Y`. The WR's paratroopa stomp needs it; no 4-2/1-1 enemy has id ≥ $07.
  • **F136 — the pipe list was wrong.** `VerticalPipe` gives EVERY vertical pipe outside 1-1 a plant (only
    `FindEmptyEnemySlot` refuses), so the dump-derived list was a lower bound. Room 2 = (115,9) (122,8)
    (132,9) **(142,8) (152,4 — the clip pipe itself)**. `W84_ROOM3_PIPES`' old (228,6) is not in BB84 and
    must be re-derived before room 3's enemies are wired.
  • **Validation**: WR **267/267 frames exact** vs the core incl. both enemy events, same pipe-entry frame;
    `--check-path 267` = GOAL at step 267, **0 bound violations**; **900 random trials / ~171k frames, 0
    differences** (`runs/P2.2f/batt_seed{7b,11,3}.log`). 4-2 regressions both pass: the `--lift 0` control
    gate exact (6/16/34/70/134/673/3472/16472/69489/257001) and the F127 chain 596/596, 0 mismatches.
  • Case changes the port forced: `WithScrollPos` + `WithBlockBounceTimer` + `W84Room2Blocks` (key 11 → 20
    bytes; PARSER_COL0 136, IP0 1, FC0 120, GT0 24, CELLS = the one hidden block (150,7)); a non-empty
    start ext (`w84_room2_ext0()`, 3 plants + 2 beetles + loader at eoff 18/page 8) so `ext0` plumbing now
    carries a full `Ext`; and a **latent shared bug fixed** — `BlockStateData::parser_col` is a u8 but only
    7 bits were packed, so 136 round-tripped to 8 (4-2/1-1 both start at 24, so nothing had noticed). The
    top bit moved into a spare bit at the END of the field: every existing record stays byte-identical.
  **THE SEARCH: two proof-grade verdicts, one clear blocker (F137/F138/F139).**
  • **F137 — the x-only bound cannot carry the tail.** It is satisfied at floor level ~15 frames before the
    goal, so h = 0 across the climb. Added a y-coupled `YGate` over the goal's NECESSARY condition
    `x >= 2436 && Player_Y <= 64` (`W84R2_PIPE_Y`). Trap: `steps_xy` scans from k = 1 so it never returns 0
    and prunes the WR's own goal — states already satisfying the condition get h = 0 explicitly. Audits
    clean (0 bound violations on the WR; `ygate_audit --mutate` 1335 checks / 0 violations / min slack 0).
  • **F139 — THE WR's LAST 47 FRAMES OF ROOM 2 ARE OPTIMAL (proof-grade).** The right shape is the one
    P2.3c-11a already argued: root on the WR's OWN state and search the tail **exhaustively** (no beam), so
    a dry is a verdict and a goal is a real improvement. Rungs: prefix 240 **d27 = positive control**
    (goals at layer 27, reference GOAL, 0 bound violations); prefix 240 **d26 DRY** (~10 s); prefix 220
    **d46 DRY** (209 s). **Seam map measured in the WR: MrWint's boundaries are at step 70 (x 1981) and
    step 227 (x 2373).** So the d46 rung SPANS the x-2373 seam ⇒ **that seam is not leaking a frame** —
    a real, negative, H42 answer. Cost wall between d46 and d56: prefix 210/d56 hits 9.9M states at layer
    14 (x2.7/layer, `pruned 0`); prefix 200/d66 x3.3/layer. F98's law at 14 frames of slack.
  • **F138 — a beam is the WRONG TOOL for this room, and `--check-path` is what proves it.** It reports per
    layer whether the reference path is still in the frontier. The beam drops the WR at **layer 40** from a
    step-0 root and at **layer 41** from a step-70 root — the same ~40 layers in regardless of where it
    starts, at widths 50/200/2000/3000 and with a new absolute-x bucket axis. Cause: the bound is loose by
    **14 frames at EVERY root** (probes at steps 70/180/200/220/240 give slack 14/14/14/14/13), so h-first
    ordering systematically prefers the family that is AHEAD of the WR on x. Width and bucket diversity
    cannot compensate. (An enemy-config axis `--beam-buckets e` was added for H40 at the same time; not the
    blocker.)
  **CONTROL-RULE CORRECTION (user, this session).** "Do not run d266 until the d267 control passes" was
  wrong for the goal. A control only tells you what a DRY means; a d266 run that finds a path is a record
  regardless. Since both cost the same, **run the real deadline and piggyback `--check-path` on it** — you
  get the hunt and the trustworthiness readout in one run. Applied from now on.
  **NEXT UNIT — the coupled end-game term (this is the whole blocker).** All 14 frames of slack sit in the
  last 27 frames: at the WR's step 240 the bound says **13** and the truth is **27**. Cause: the bound takes
  `max(x-cost, y-cost)` as independent when they are coupled — Y <= 64 is only possible while standing on
  the cap (x in [2432, 2464)), and you arrive there at ~0 speed, so the last 13 px are WALKED from a
  standstill while the x table prices them at full running speed. **NOT room 3's `build_overshoot_bound`**
  (that is an x-overshoot-and-return table — wrong geometry). Build a small exact end-game table over the
  last ~30 frames indexed by (Y, y_spd, v_force, x, x_spd) by backward search on the real model; the
  prefix-240 rung searched that region exhaustively in ~10 s, so it is affordable. Collapsing the slack is
  worth ~x3 frontier per frame recovered — the difference between a 47-frame exhaustive reach and one deep
  enough to answer the x-1981 seam outright.
  **USER'S STANDING QUESTION (answered, keep in view):** the edge is only at the seams, and one of the two
  is now closed. Room 2's remaining hope is the step-70 seam; the 157-frame middle is at the speed cap
  (F67) and the first 70 frames are MrWint's own exhaustively-searched `W84Part2Speedup`. If the end-game
  term does not open the step-70 question, **room 2 should be declared closed and the effort moved on.**
- **P2.2a — H25, the 8-4 turnaround-room stop (started 2026-08-24 session 14 evening; the
  campaign opener per the new decisions.md priority).** Step 1: dump forensics — the (14,4)
  area-change command parses at SL ≥ 3345 (row 16516 in the WR); measure the WR's max SL margin
  over 3345 and the stop/turnaround timing (rows 16480–16560); margin ≥ ~3 px ⇒ a 1-frame-earlier
  stop still warps ⇒ the frame is real ⇒ step 2: the exact-model segment search (W84 cases,
  land room). Acceptance in the Next-up row.
  **CHECKPOINT: forensics DONE — the WR's margin over SL 3345 is ZERO px** (SL hits 3345 and the
  $02 command parses on row 16516 exactly; max x 3457 = rel 112 pinned; a hand-tuned brake with a
  re-accel blip at 16503 — HappyLee optimized this to the pixel, so the H25 frame lives in the
  brake's subpixel phase / the seam into the F66-optimal 74-frame clip). **The case `W84Room3`
  is BUILT** (Small + scroll, goal = pipe (212,5) with screen_left_abs ≥ 3345, F89 overshoot
  bound; MrWint's clip case independently encodes the same SL window — threshold cross-checked).
  **WR line 195/195 exact — but the random battery FAILED (9/100): room 3 is NOT enemy-free.**
  The core has **3 piranha plants (one IN the warp pipe — the WR enters via F100's $21 distance
  rule) + the flying-cheep-cheep FRENZY** (id $14, LFSR-driven = frame-indexed on the lag-free
  route); the t2 divergence = a cheep stomp bounce (kept inputs `runs/P2.2a/keep_s5/`). Bound
  horizon fixed 0 → 96 (the premature d194 was slack-29 and killed). **NEXT: port the plant
  class from w42enemies + model the cheep frenzy (asm: FlyCheepCheepFrenzy/InitFlyingCheepCheep/
  MoveFlyingCheepCheep) into a `w84enemies` hook, difftest to 0 incl. cheep stomps, THEN the
  d194 rung `--enemies` + d195 check-path control.** `P2.2a-84-turnaround.md`.
  **CHECKPOINT 2 (session 15) — the room is now CUT AT THE APEX and the return leg is CLOSED (F125).**
  Cutting at the WR's apex (max x 3457, record 16516 = prefix 162) gives a 33-frame tail: control
  `… 16354 162 33 --check-path 33` = `at root: Some(33)`, 0 bound violations, **96 goals at layer 33**;
  record rung `… 162 32` = **dry at layer 1**. h(apex) = 33 = the WR ⇒ zero slack ⇒ **H25's frame is
  NOT in the turnaround/return** — it is in the approach or in reaching a different apex state.
  Fixed a real bound hole: `W84Room3` returned `Some(0)` for every state with SL ≥ 3345 and
  x ≤ PIPE_XMAX (admissible but never pruning — the `pruned 0` on every room-3 rung); added
  `W84R3_PIPE_XMIN = 0xd4400` from the F124 foot geometry + the leftward branch (patch regenerated).
  **Whole-room d194 is infeasible** (root 183 vs 194 = slack 11; horizon 96 → 200 leaves it at 183, so
  the looseness is terrain + pipe-entry y-coupling, not truncation — F95 confirmed for 8-4).
  **NEXT (not the enemy port):** segment the APPROACH (root → apex, 162 frames) — either a y-coupled
  /ygate-style bound, or a further cut at the brake start (WR row 16492, x 3428) — then chain.
  **The `w84enemies` port is DEFERRED and is bigger than budgeted (F126):** the cheep frenzy spawn law
  reads `Player_X_Speed` and `Player_X_Position`, so it is NOT frame-indexed — different trajectories
  see different cheep fields. Cheapest order: find a candidate enemy-free first (a goal replays on the
  core, where cheeps are checked for ONE path), model only if a dry needs it.
  **Ops rules learned (now in the runbook):** `max_steps` counts layers from the POST-prefix root, not
  absolute frames (a prefix-162 rung at deadline 195 has 162 frames of slack — it hit 27 GB by layer
  23); and read the `--check-path` startup audit before paying for the exhaustive part.
  **CORRECTION (session 16, H39): the "segment the APPROACH, then chain" plan above cannot find
  H25's frame.** F125 proved the return leg optimal *from the WR's apex* (h(apex) = 33 = WR; the
  32-rung dry at layer 1), so the WR's apex yields nothing; an approach search whose goal IS the
  WR's apex can therefore only find "reach that same dead apex sooner". The frame, if it exists,
  is in **a different apex state** — which the apex cut deletes by construction. The approach unit
  must emit a **set** of apex-region states, each with its own return cost (multi-goal seam, or a
  multi-root return search), not a single first-arrival goal. Blocked behind P2.3c-8.

## Next up (ordered — the top unblocked item is the next unit of work)

**PRIORITY REBUILT 2026-08-25 (session 18) — see `docs/strategy-review.md`, which is now the
official way forward and supersedes the 2026-08-24 "8-4 campaign" ordering where they disagree.**
Two things changed. **(1) User doctrine: proof and exhaustiveness are no longer deliverables — we
want a record, full stop.** Beams, stochastic search and restarts are legitimate finders; only a
*positive* needs verification (core replay, then two emulators). **(2) The other session settled
that the bottleneck is the state space, not the bound** (`P2.3e-framerule-scan.md` §41: with the
bound only 4 frames loose the frontier is 36.7M wide by layer 24) — so `P2.2f-bound` is retired as
an unlock and the exhaustive-ladder programme with it. What is left is a search whose *shape* can
hold a "pay first, gain later" trade, which is Track **E** below.

| ID | Title | Track | Size | Depends on | Acceptance |
|---|---|---|---|---|---|
| E1 | **S7 — the free-knob check (do first, it is cheap).** Is level-entry state a pure function of the entry frame? Check the LFSR ($07A7-$07AE), `IntervalTimerControl`, `FrameCounter` and the frame timers across every level entry in `data/wr/fceux_wr.ram`; establish whether anything at all carries across a level boundary that is not determined by the entry frame. **If yes:** the game decomposes exactly into 7 framerule lotteries + 8-4, per-level greedy is right, and H9/P2.4 close. **If no:** the framerule levels' slack (3-20 frames each, FREE) is a zero-cost knob on 8-4's Bowser/cheep RNG, and 8-4 is the unquantized level. F62 already shows the LFSR and `FrameCounter` are not welded together (pause steps one and freezes the other). | E | S | — | A stated verdict in `docs/experiments/P4E-*.md` + H9 status; if a knob exists, its size in distinct reachable 8-4 entry RNG states |
| E2 | **The last-input reformulation of 8-4 (H1).** The movie ends at the last input (F17): WR last input 17848, axe 19 frames later. Reformulate the endgame as *"earliest frame after which the null-input continuation still reaches the axe"* — a LATER axe touch with a longer coast is a strict win, which is a different question from the one anyone has asked. Step 1 is free: truncate the WR's own input on the core and find how far back it still finishes. Step 2: search the last ~120 frames with coast as the objective (airborne frames keep the x speed ground friction eats, so a final jump whose last A-press is the last input is the shape). | E | S-M | — | The truncation curve; then a last input < 17848 that reaches the ending on the core, or the measured cost of the best coast found |
| E3 | **The Go-Explore finder on the QuickNES core (the main engineering item).** Archive keyed on a coarse cell (x band, y band, x-speed band, scroll band, block/enemy digest, frame band); per cell keep the best state under the level's own objective; loop = pick cell (weighted to under-visited / recently-improved), restore, roll out 15-60 frames of sampled input, insert. No bound, no frontier; memory bounded by cell count, not layer width. Holds "pay first, gain later" natively because the paid state keeps its own cell. Substrate exists: `build/harness` at 15.0k fps/instance, 104k fps on 12 threads, save+load 2.5 us (F46). Runs on the REAL emulator, so no model-gap class (F147/F149/F150) and every path is core-verified by construction. | E | L | E0 substrate | A driver in `src/fastcore/` that reproduces a known optimum (4-2 main 553, or 1-1 room 1 368) from a cold archive, then is pointed at 8-4 |
| E4 | **Point the finder at territory nobody has pinned.** Order: **1-2's 540-frame intro** (fceux rows 1946-2486 — never modelled by anyone, and Maru's 3-frame advantage over the WR in 1-2 has to be somewhere), 8-3 (deficit 7 with FPG), 4-1 (9), then 8-1/8-2. Whole regions, seam-free, no intermediate goals — the gate is the thing that deletes the answer (H39). | E | L | E3 | Best-found per region vs the WR, with the archive kept so a later run resumes rather than restarts |
| E5 | **Re-rank every reachable area by card / quantization / timer reload / distance to the axe.** H44 has never been asked with those columns filled in. `DisplayIntermediate` skips the card when `AltEntranceControl != 0`, or `DisableIntermediate != 0` and `AreaType != 3`; `DisableIntermediate` is set by `IntroEntr` gated on the DESTINATION area's `PlayerEntranceCtrl` = 6/7 header bits — a ROM constant readable with `tools/area_data.py`. An area entered without a card is also **unquantized**, worth ~117 frames plus the framerule. Only Track B work with a frame attached to it. | B | S-M | — | A table in `docs/warp-model.md` with the four columns for every area reachable by any known or hypothesised redirect |
| P2.3c-9 | **F131 — model the wrong-warp ENTRY FRAME, then ladder the top-route warp cost.** Part A (was 'small', is not): the warp needs the entry frame's latched `Player_X_Scroll` to be 0 (F129), but that frame is one the search does not simulate — the model's goal fires when Mario *reaches* the entry x (the WR's own goal step has d = 2), so a goal-side `SL + 48*d <= 1216` test **rejects the WR's own warp** (F131, verified). The fix is case-level: make the goal fire on the entry frame under Down (or carry one extra simulated step), not a refusal tweak. The sound necessary condition `screen_left16 >= 1217` is what ships today, so **the search still emits candidates that do not warp** — the core-replay destination check (runbook §4.3) is the gate. **Part B — the exact shape of the search (do NOT run a whole-level pass; F132 proved that fails).** Root on the known 553 chain at one of the G-line cumulative points — the G-line is 149+184+82+34+35+25+44, so the roots are prefixes **415 / 449 / 484 / 509** (= 138 / 104 / 69 / 44 frames from the pipe). Horizon = (553 − prefix) + slack, laddered **downward** until dry: from 509 that is d87 (the F127 result) → d84 → d80 → d76 → d72; if the ladder bottoms out above 22 frames of key cost, step the root back to 484 and repeat, because a cheaper mint may need a different *arrival* state at the wall and a fixed root pre-commits it (the seam problem one level up — F123's ops lesson was already "root ≥ step 200"). Short horizon (tens of layers) is what lets the bucketed beam be wide enough to matter, and it is the same shape as P2.3c-11a. Every goal core-replayed + destination-checked. | A | M–L | — | Part A: the reference-path audit still marks the WR's warp GOAL **and** a d>0 entry is refused; beam-off gate byte-identical. Part B: a measured minimum top-route key cost vs the 22 the 575 line allows, with the root stepped back until the number stops improving |
| P2.3c-10 | **Re-audit every beam-derived verdict with `--beam-buckets` (F128).** Any conclusion resting on "the search never found X" was produced by a single-key beam. First: **F123's bottom-route mint economics** (`mint_cost_beam.log`, 2M offset-first) — its 27-frame minimum mint and the 584-585 floor gate the whole "4-2 closed both ways" claim. Then the F122 table's remaining rows. | A | M | P2.3c-9 | Per-verdict: the bucketed rerun's number vs the original, and an explicit statement of which conclusions survive |
| P2.2a′ | **8-4 room 3: the multi-apex seam, ENEMY-FREE FIRST (the real next 8-4 unit).** F125 proved the return leg optimal *from the WR's apex* (h = 33 = WR, the 32-rung dry at layer 1), so H25's frame can only be in **reaching a different apex state** — which an approach search goaled on the WR's apex deletes by construction (H39's seam corollary). Search the 162-frame approach with **generic** buckets (mechanism unknown ⇒ discovery keys, H40) including an apex-band axis, emit a **set** of apex-region states, and compute the return cost for each. Run it **enemy-free** and let the core adjudicate the plants/cheeps per candidate (the F126 cheapest-order note, line 117): one core replay checks one path exactly, which is far cheaper than modelling the frenzy up front. | A | M | — | A set of ≥1 non-WR apex states with per-apex return costs; either a 32-frame return from one of them (= the H25 frame, then the record pipeline) or a dry across the whole set |
| P2.2f-bound | **IN PROGRESS (s17). Part 1 built and controlled; part 2 identified precisely — see experiment §37.** Part 1: `Surface.embedded` (a standable cell with a solid cell above it, so Mario is inside terrain and arrived at `x_spd = 0`), keyed per **(y, embedded)** interval, with the faster jump classes charged `accel_frames` (29 running / 18 walking). Controls green: 4-2's gate byte-identical, 8-4's reference path 0 violations. **The slack did not move (still 15, 13 of it at steps 246-248)** because `T(Y96) = 6` comes from a **chain through a surface the trajectory only passes while RISING** — `hold_terms` credits a landing at any frame the height matches, ignoring `y_spd`. **Part 2 REDIRECTED by measurement (experiment §38).** `SMBOPT_YGATE_EXPLAIN` dumps the gate's reasoning; at step 245 it is `max(tr 7, x 8) = 8` against a truth of 22. **A unit error had been driving the plan:** `x_spd >> 8` is in **1/16 px**, so the cap is **2.5 px/frame** and `gain(8) = 20 px` for `dx = 18 px` — **the x table is exact here, and so is the necessary condition** (the WR first satisfies `x >= 2436 && Y <= 64` on the goal step itself, and from step 246 the bound tracks the truth to a frame or two). **All 13 frames are the four airborne frames 242-245, where the gate charges `max(climb, walk)` for something that is `climb + walk`.** The obvious serial term — `h >= t_clear + steps(gx - wall)` — would recover ~9 but is **UNSOUND and must not be retried**: `BB84` rows 8-10 are empty under the pipe with a full floor at row 11, so Mario can go *under* and a lower bound must be the min over routes. **Part 2 BUILT AND AUDITED (experiment §39): the `Blocker` term.** A maximal solid run in a column; Mario cannot hold `x_pos > x_lo` unless his Y is above it or below it, so the cost is the **min over the two routes**, each serial — which asserts no impossibility and so stays admissible. Opt-in via `YGate::with_blockers`, so every other gate is unchanged. **Audit: 2000 trials / 6,942 admissibility checks / 0 violations, min slack 0**; 4-2's gate byte-identical; 8-4's reference path 0 violations. **Effect: slack at steps 240-245 cut 14 -> 8, at 235 15 -> 13; from 246 on it was already 1-4. Root slack UNCHANGED at 15.** **And the unit's premise needs revisiting (experiment §40).** At the root the y gate is irrelevant (`kd = 26`) and the binding term is the **x table**, which already models the acceleration ramp correctly (251 frames for 588 px). A serial decomposition of the WR's end-game comes out at ~250, i.e. BELOW what the bound already has — nothing to recover. And `kd = 26` means a running jump reaches `Y <= 64` **mid-air with no platform**, so the necessary condition can be met mid-jump (the WR meets it on a FALLING frame). **So the 15 frames may be the honest gap between the relaxed problem's optimum and the WR's cost, not looseness — in which case no gate work closes them and the '<= ~2 slack' acceptance criterion is the wrong target at the root.** **PROBE RUN, and it reframes this whole unit (experiment §41).** `--goal-x 2436 --goal-y 64` from prefix 200 (WR needs 67, bound says 52): at **d60 (slack 8)** 19.4M states by layer 22, x2.7/layer; at **d56 (slack 4)** 36.7M by layer 24, x2.0/layer, 10 GB — both killed without a verdict. **Even the relaxed problem, with the bound 4 frames loose, is 36.7M wide 24 layers in.** So F98's law holds but the constant is brutal: slack 4 buys ~24-30 layers, slack ~1 buys the ~47 F139 achieved. **The open question here — the x-1981 seam — is 197 frames out, so no bound will put it in exhaustive reach. It is a state-space problem, not a bound problem.** The bound work stands on its own merits (late-layer pruning) but this unit should NOT be continued in the hope of unlocking the seam. **The lever that is left is a better BEAM, not a better bound** — an ordering that does not delete the 'pays before it gains' family that F138 showed beams drop. Runbook §7.5 / H41's untested idea (score exit-state quality, make time a hard constraint, instead of ranking on `h` where `h` is flat) is the next unit, and it is the same wall §35 hit in 1-2 — so it would unblock both. Do it behind `tools/ygate_audit.py` — an inadmissible bound silently prunes the improvement we are hunting. **Motivation is DEPTH, not proof** (user, s17): we have no systematic record of dry segments, so a dry banks nothing; the tighter bound is worth building because it lets searches reach depth and *find* things. **The three-level payoff below still stands.** 1-2's joint d199 search has **53 frames of bound slack**, and `--check-path`'s per-step `h` localises every one of them (experiment §34): **cluster A ~30 frames** at the wall clip (Mario is *inside* the wall with `impede_player_move` resetting his speed, so 11 px take 19 frames where the x table prices 40 px/frame — this is HORIZONTAL, a `YGate` does not touch it) and **cluster B ~21 frames** at the end-game turnaround, taken airborne off a warp-pipe cap, which `build_overshoot_bound` cannot see. The 88 frames of open running between them lose **one** frame total. Both clusters want the same construction as 8-4 room 2's below: a small exact table over a localised region by backward search on the real model. Do 8-4's first (spec below), then apply the same machinery to 1-2's two regions. **The 8-4 spec:** The port is done and the room has two proof-grade verdicts (F139: the WR's last 47 frames are optimal, and that rung crosses MrWint's x-2373 seam, so **that seam does not leak**). What is left is the x-1981 seam at step 70, ~197 frames out, and it is unreachable because the bound is loose by **14 frames at every root** — which also makes any beam drop the WR's own path ~40 layers in (F138). The slack is located exactly (`runs/P2.2f/wr_hprofile.txt`, experiment §13): it is **entirely in the airborne approach** and collapses the frame Mario lands (step 245 h 8 vs true 22; step 246 h 17 vs true 21; tight from 247 on). Cause: the gate reaches `Y <= 64` through its Y-96 surface with `t_surf = 6`, a *running* jump's arc — but the Y-96 wedge exists only because Mario hit the pipe's left wall, so he is there at `x_spd ~ 0`, the weakest jump (the WR's climb takes 10 frames), and then walks the cap from the same standstill. Build a small exact end-game table over the last ~30 frames indexed by (Y, y_spd, v_force, x, x_spd) by backward search on the real model — the prefix-240 rung searched that region exhaustively in ~10 s, so it is affordable. **NOT room 3's `build_overshoot_bound`** (x-overshoot-and-return; wrong geometry). Payoff: ~x3 frontier per frame of slack recovered (F98), i.e. the difference between a 47-frame exhaustive reach and one deep enough to settle the x-1981 seam outright. | A | M | — | `--check-path 267` slack <= ~2 over the WR's last 40 steps with 0 bound violations; then the prefix ladder re-run, with the deepest rung that completes recorded |
| P2.2a-port | **Model the cheeps — ONLY IF P2.2a′ goes dry enemy-free.** F130 makes it cheap; do not pay for it before the enemy-free pass has failed (F126 cheapest-order). F126 deferred the port as "materially bigger than budgeted" because the cheep frenzy reads `Player_X_Speed`/`Player_X_Position`. F130 (verified in the disassembly) shows speed enters as a **3-valued class** and position is an **additive, player-relative** spawn base — not a branch. So the frenzy is frame-indexed up to a 3-class: port cost ≈ 3×, not 2^k. Port the plant class from `w42enemies` + the frenzy with the F130 key (`FrenzyEnemyTimer` phase, speed-class, slot occupancy), difftest to 0 incl. cheep stomps. | A | M | — | Difftest 0 diffs over a random battery incl. cheep stomps (the 9/100 battery that failed in P2.2a now passes); then the d194 rung is unblocked |
| P2.3c-11a | **Dissolve ONE 4-2 seam at a time (the corrected cross-seam test, F132).** The whole-level single-pass beam failed: no goal at deadline 575, frontier stalled 8 px short of the pipe — ≥22 frames worse than the chained 553, and the pre-registered reading makes that *uninformative* about seam leakage (runbook §7.2). Widening it to segment-search density over 575 layers is ~165 GB. Instead root on the known chain **two segments back**, set the deadline to those two segments' known combined cost, and run a **wide** bucketed beam over the resulting tens-of-layers horizon. Repeat per seam (the G-line is 149+184+82+34+35+25+44). Informative in both directions: a result under the known combined cost means that seam was leaking on a level certified "every segment at its bound", which would reframe every closed level — and 8-4 is where one frame IS the record (H24). Also the natural place to test H41. | A/infra | S–M | — | Per seam: the known combined cost reproduced (machinery sound) or beaten (seam was leaking), core-verified; plus an H41 verdict |
| P2.3e | **Next framerule level with the existing tooling (the default, B).** Candidates by remaining deficit: 8-3 (10, of which F37's FPG-242 gives 3 → 7; Hammer Bros are RNG-driven and the model has no RNG), 1-2 (8 on the WR's route, 5 on Maru's, H22), 4-1 (9). First unit = a one-session feasibility scan of all three (block maps from the dump via `tools/blockmap_from_dump.py`, enemies from `tools/area_data.py`, model gaps, which segments are RNG-free), pick one, then a case in the patch + difftest + bounds + ladder as done for 4-2 (`P2.3a` → `P2.3c-2c` pattern). | A | L | — | Scan table in a new experiment file with the chosen level and why; then a case exact on the WR's frames and a first segment bound vs the WR |
| H37 | **Pipe B floor-level entry test** (4-2, cols 78–79): `bfscx --goal-x 1262 --goal-y 176` from a grounded root in front of pipe B (a census pick at x ≥ 1200 from the 509 chain's predecessor layers, or a WR state) with a small ladder. A path = a new route (replay on the core, F80-style); a dead frontier = the col-78 face is a sound gate. Never reached by any run so far (F117). | A/B | S | — | A core-replayed path or a proof record in hypotheses.md |
| P3.2 | **RAM oracle:** single-byte perturbation sweep per level on the fast core → jackpot map (Track B must not starve — PROCESS). Targets sharpened by F43: WorldNumber ≥ 7 before an axe; AreaPointer/EntrancePage = $65/16 before a down-pipe; WarpZoneControl ∈ {2,6} in 1-2. | B | M | P1.1 | `docs/experiments/P3.2-ram-oracle.md` with the cell list; H7 status updated |
| P0.11d | **Fold the Mac fan-out lessons into the two-box docs + fix the Mac watchdog** — the list is `docs/experiments/P0.11-two-box.md` §7 (13 items; #4 and #13 done). Biggest: the watchdog must `docker kill` its container (#11); `watchdog.sh` dying silently (#6). | infra | S | — | PROCESS §parallel-work updated; `tools/watchdog.sh`/`mac_run.sh` kill the container; a deliberate over-cap test on the Mac shows the container gone |
| P2.3c-4 | **Sound dominance pruning / frontier abstraction in `bfscx`.** Drop states dominated within a layer (same frame, block/enemy state; position/speed provably at least as good) with a per-case soundness argument; and, for the wrong-warp finale, collapse the 64-byte enemy ext where no live enemy can touch the state. Note (session 13): the finale's multiplier is the mint state, not the enemy ext — this lever helps the proof runs generally but is not expected to rescue d62–d66 alone. Measure on S1 d149's layers. | A/infra | M | P2.3c-1 | Soundness note in `P2.3c-engine.md`; layer counts with/without on the S1 control; the reference path survives |
| P2.3c-2b | **Warp-zone end-game (x,y) bound + the warp-zone run** (H35): the 15 frames between the coupled bound 461 and the WR's 476 are all in the drop/fall/landing; a Phase-B multi-root search from all drop states or an end-game bound so the frontier stops growing ×1.25/layer. Only matters together with a main-area framerule. | A | M | P2.3c-2 | Warp-zone optimum with a proof record vs WR 476 |
| P0.11b | **Measure the Mac's real expand throughput** (`--resume` one xz'd run-4 layer at `--threads 12`, states/s from the `expand` field vs the laptop's 8.75M/s at 12). The only datum so far is P0.11 §7 #10 (≈ 0.84× per thread), which contradicts F106's 2.8× proxy. | infra | S | — | A measured states/s recorded as a fact superseding F106, added to the P0.10a table |
| P0.10a | **Benchmark the reachable Hetzner tiers (< $1)**: cx53 16c ($0.0561/h), cpx51 16c ($0.1338/h), ccx33 8c ($0.2612/h) — build, run the `bfscx` control gate, `--resume` a run-4 layer, record states/s; delete every box the same hour (F95). Check whether shared tiers are quota-limited first. | infra | S | P0.10 | A throughput/$ table in `P0.10-cloud-sizing.md` §8; go/no-go on shared tiers |
| P0.11c | **(optional, timeboxed) Port `smb-opt` off `nightly-2018-06-01`** — removes the container requirement, native arm64 on the Mac. Engine work ⇒ primary box only. Abandon if not cheap. | infra | M | — | Control gate identical on a native build; timebox outcome in `P0.11-two-box.md` |
| P2.3c-3 | **(parked until a core-limits increase)** Parallelise `bfscx`'s k-way merge by key buckets (F96: merge is 4–6 % of wall at ≤ 16 cores; worth it at 32+). | infra | M | P0.10a | Merge wall time scales with `--threads`; layers byte-identical |
| P2.2 | 8-4 exhaustive search (frame-granular; Bowser RNG, L+R, the ending-input coast H1; Maru's turnaround-room idea H25). F67: every running/swimming section is at the speed cap — remaining levers are transitions, the water-room end alignment, Bowser/RNG, glitches. | A | L | P2.1 tooling | Faster path verified in two emulators, or a proof record |
| P2.4 | Cross-level DP over reachable entry states (RNG / framerule phase, H9). | A | M | P2.2, P2.3e | Best-known full route + proof record |
| P1.2 | Stage-2 core (static recompilation of the ROM with cycle counting + minimal PPU timing) — only if a whole-level exact search ever needs it; the model route (P1.2-lite + patch) has carried everything so far. | A | L | P1.1 | Differential test vs QuickNES on ≥ 10M random frames incl. lag |
| P1.1b | Direct-link core: build Nes_Emu into the search binary, `emulate_skip_frame`, keep RAM identity vs F45. | A | S | P1.1 | ≥ 2× fps over F46 on the WR RAM trace |
| P3.3 | Write-reachability: H30 refuted for vines; remaining = any other writer above Y $20 at an odd-page column 11/12 (enemy block bumps, coin erases); then the P3.2 jackpot cells. | B | L | P3.1 | Ledger entries with proof artifacts |
| P3.4 | Fuzzing / Go-Explore novelty search for anomalous states. | B | L | P1.2 | Anomalies triaged in the ledger |
| P3.5 | NES Minus World re-examination with oracle + audit (WorldNumber = 36 OOB reads). | B | M | P3.1, P3.2 | Ledger entry with proof artifact |
| P4.1 | Assemble, verify in two emulators, draft submission text. | ship | M | a result | User-reviewed before anything is submitted |

Wrap-up items (fold into whichever unit touches them first): **The `IgnoreCoins` audit (F147's bug class) is
CLOSED — the bug was 1-2-only.** The engine already models both coin paths: `note_coin_award` (the
`AwardTouchedCoin` metatile path) and `fresh_bump` (any block bump) each set `vbuf1_busy`, which stalls the
parser. `IgnoreCoins` breaks only the first, by reporting every `$c2` cell as already collected so a touch
never awards. Swept: **1-2 was broken and is fixed** (F147); **4-2 has a real handler**, so its metatile
coins award normally; **8-4 room 2 has no `$c2` cell**; **1-1's `BB11` has none either**, and the coin its
room-1 route does award (fceux f347, CoinTally 0 -> 1) comes from a **block bump**, which `fresh_bump`
covers — so **F124 is clear**. Worth keeping: the trap that made this hard to see is that 1-2's **150-trial
battery passed with the bug in it** — a battery compares Mario's fields, and a mis-timed plant only reaches
Mario in rare configurations. Only the core replay of a searched path found it.
Other wrap-up items: **F139's 8-4 rungs are re-verified on the bbox-fixed engine — all three identical**
(control 436,334 goals to the digit, d26 dry, d46 dry at root bound 32), so F139 stands in full.
Other wrap-up items: audit the truncated goal-parent
print (`main.rs:987`; the census-by-prefix workaround is in the runbook); `bfs11cr` grab
bookkeeping is unbounded in the pole zone (4 OOMs in run 4 — count non-FPG grabs, key only
FPG ones); the 552-vs-553 optimality note (at most one frame open; a third framerule would
need 533); update the explainer page (`docs/web/README.md` — its results table hardcodes
149/184/82/415; needs 553 and the warp-key finding).

## Done (one line per unit, newest first; details in the pointed file)
- 2026-08-24 s16 — **P2.2a′ — 8-4 room 3 reduced to ONE question; strong negative, not proof (F133).**
  (a) **No mint in room 3** (census: max offset 112) ⇒ `SL >= 3345` forces `x >= 3457`, the case's own threshold.
  (b) **The return floor is 33 across the WHOLE space** — `build_overshoot_bound`: 30,720 end classes, return costs
  [33..39] — generalising F125, which only had the WR's own apex. (c) **The WR crosses x 3457 at step 161 and
  finishes at 195 = a 34-frame return**, where the cheapest class pays 33. **That 1-frame gap is exactly H25**, now
  precisely posed: *is a 33-cost end class reachable at step <= 161?* (d) Answer so far **no**: diversity-beam
  approach → 2,303 apex candidates → exhaustive continuation dry (extinct at layer 188); re-run at 5x width with a
  finer key + `vf` axis → **4,333** candidates → **dry again, identical death point and max x**. Convergent, but
  layers 1–162 are beamed, so not a refutation. Proof-grade needs the exhaustive approach (slack 13 ⇒ cloud).
  Also: `offset-census` extended to `W84Room3`. `docs/experiments/` via F133.
- 2026-08-24 s16 — **P2.3c-9 Part A attempt + P2.3c-11 cross-seam test — two negative results, both useful.**
  (a) **F131**: the F129 warp condition cannot be a goal-side refusal — `SL + 48*d <= 1216` **rejects the WR's own
  warp** (the model's goal fires when Mario *reaches* the entry x, d = 2 for the WR; the core's entry frame has
  d = 0). Reverted to the sound necessary condition. **The `--check-path` control was not applying `goal_refused`
  at all** (`main.rs:1023`) — a bad refusal could have rejected the WR silently; fixed, and that fix is what caught
  it. Part A re-sized S → M–L (case-level: fire the goal on the entry frame). (b) **F132**: the whole-level
  single-pass bucketed beam found no goal at d575, stalling 8 px short of the pipe — the *uninformative* branch by
  the pre-registered reading; the seams encode too much structure for a naive whole-level pass at 3e5/layer.
  Corrected design queued as P2.3c-11a (one seam at a time, short horizon, wide beam).
  (c) **Engine safety**: runbook §5 **Rule 0 — never commit inside the clone** (a commit moves HEAD off the pin, so
  `git diff` regenerates an EMPTY patch, `git apply` succeeds, and the Mac silently builds unmodified upstream) +
  `tools/regen_patch.sh` with HEAD/pin, intent-add and shrink guards. Prompted by a real near-miss this session.
  `docs/experiments/P2.3c-8-beam-diversity.md`, F131/F132.
- 2026-08-24 s16 — **P2.3c-8 — BEAM DIVERSITY: the search method itself was losing solutions, and it cost us F122.**
  H39 confirmed (F128): `--beam N`/`--beam-offset` are global single-key orders = per-layer first-arrival gates,
  the same lossy operation as a segment seam applied every frame. Shipped `bfscx --beam N --beam-buckets
  off,y,spd,sub[,vf] [--beam-max M]` (best N per physical bucket; `--beam-max` shrinks per-bucket width first and
  logs `WARNING capped` if it ever drops whole buckets) + `smb-opt offset-census CASE LAYER_FILE` (pick_parent.py
  cannot decode `left_screen_edge_pos`). **Regression: beam-off byte-identical** (control gate 6/16/34/70/134/673/
  3472/16472/69489/257001). Re-ran F122's own probe: offset **112 -> 132**, a **core-verified** pipe entry at 596
  frames (87/87, 0 mismatches), mint maneuver = 19 frames of held Left. **F122 refuted (F127)**; two of its five
  rows had never measured the offset. **But the warp is still wrong (F129)**: the sct-freeze mint is transient, the
  scroll catches up during the descent, and the warp needs `Player_X_Scroll` = 0 at entry — an unmodelled second
  goal condition, so every wrong-warp GOAL the engine reports is suspect. H36 reopened; F123's closure caveated.
  `docs/experiments/P2.3c-8-beam-diversity.md`.
- 2026-08-24 s15 — **P2.5b-1**: **H29 refuted proof-grade — 1-1 room 1 is optimal at 368 with the enemies (F124)**. The d367 rung is dry in 4.7 s (root bound exactly 367, frontier 1→36 then extinct at layer 21); admissibility proved at code level (pipe entry forces `x_pos ≥ 0x39400` via the right-foot `cv 0x11` adder 0x0c00 = exactly the case bound's target; `w11enemies.rs` never references `x_pos`/`x_spd`, only the stomp bounce). Positive control = the reference-path audit that runs *before* layer 1: WR line → `StateChangeVerticalPipe(57,7)` GOAL at step 368, **0 bound violations / 368 steps**. The d368 *exhaustive* rung was stopped as infeasible (94 GB at layer 90/368, ≈1.6 TB projected) and was never needed; 94 GB reclaimed. **H21 closes too** — 1-1 is done end to end. `P2.5b-room1-search.md` §"The verdict".
- 2026-08-24 s14 — **P2.3c-7**: the vine-snap mint refuted at code level (kill criterion (a), same-session): every 4-2 vine grab is an irreversible autoclimb warp commitment (side-point grabs × rows-≤2 cells ⇒ Y < 32 ⇒ GES 1 ⇒ forced Up ⇒ area change to $2F), and a leave-able grab would net ≤ +14 px at wall-mint rates (~578–581 > 575); H38's x-writer enumeration completed ⇒ **H38 refuted for 4-2 — the level rests (F122 + F123 + this)**. Pivot queue: **1-1 room-1 H29 (deficit 1, exhaustive-sized at d367, port w42enemies classes) → 1-2 → 8-3**. `P2.3c-2c-main-area.md` §P2.3c-7.
- 2026-08-24 s14 — **P2.3c-6b**: `--goal-offset` mint-economics probe — min 132-mint = 27 frames but speed-priced (the WR's sct-frozen sprint already ~optimal); continuation probe ≥ 584 > 575 ⇒ **the bottom route is closed too (F123)**; 4-2 = 553 movement + ~31 key + ~4 slack, conserved. Mac: resync d679bb8 + gate exact, 401 GB stale layers reclaimed (133→533 GiB). H38 added (speed-preserving mint, parked). `P2.3c-2c-main-area.md` §P2.3c-6b.
- 2026-08-24 s14 — **P2.3c-6**: `bfscx --beam N [--beam-offset] [--log-offset]` added (opt-in heuristic finder; **optimal mode byte-identical with beam off**) to *find* a top-route warp by loosening optimality (user decision). Result: **F122 — the top route CANNOT mint the +20 px offset the warp needs** (offset frozen at 112 across 5 beam+exhaustive searches; the col-30 floor wall walk is a bottom-route mechanism; F117 blocks floor access). Strong evidence the top-route warp is structurally infeasible → **retires the P2.3c-5 cloud fork**. `P2.3c-2c-main-area.md` §P2.3c-6; F122.
- 2026-08-24 s14 — **STATUS cleanup**: narrative archived (`docs/archive/`), standing rules → `docs/search-runbook.md`, Mac lessons → `P0.11-two-box.md` §7.
- 2026-08-24 s13 — **P2.3c-5**: scroll-aware drift bound (`heuristics::drift`, F121) makes the wrong-warp finale decidable; **d58 proof-grade dry**; d62/d66 cap-killed at ~10⁹ states (not verdicts) → the fork. `P2.3c-2c-main-area.md` §P2.3c-5, §"The verdict", §"The resource wall".
- 2026-08-24 s12 (pm) — **Emulator round 1** of the 553 movie (`tools/splice_fm2.py`, `w42_553.fm2/.bk2`): FCEUX frame-perfect on the main area (552/552, entry Δ 35 rows) but the wrong warp diverges — the case goal never constrained the screen (F40); **the scroll offset is a latch minted only by collision push, the WR mints +21 px in its col-30 wall (F120)**; both conditions now refused in the hook; G4a/G4b split retired. §"Emulator verification round 1", §"The scroll-offset discovery", §"The drift geometry".
- 2026-08-24 s12 — **P2.5c-3 — THE 553**: vine modeled + validated (oracle 0/586, difftest 0/60 through the bump); G-line 149+184+82+34+35+25+44, every segment at its bound, core-verified entry at record 7136 (F118/F119; H34 confirmed, H36 confirmed beyond the claim). §"THE 553".
- 2026-08-24 s12 — S3′ ledge fault fixed (F117), G1–G3 at the bound, chain 509 core-verified (= the WR's step-540 state 31 frames early); bump-free G4 refused d44–47 — the wrong-warp plant is the gate; H34 unparked with the vine design (`P2.5c-w42-enemies.md` §"H34 vine design"). §"Session 12".
- 2026-08-24 s11 — **P2.1b-m3 / P2.1b done**: run 4 (whole-room exact search, relaxed model + goombas, deadline 238, 8 disjoint slices for layers 235–238) finds no FPG grab ≤ 238 → **H28 refuted (F116); 1-1 closed** (H29 parked). `P2.1b-pole-search.md` §"Run 4 verdict".
- 2026-08-23/24 s11 — **P2.5c-2 step 5, the enemy-aware chain**: S2 = 166 (F112), S2′ = 184, S3′ = 82 (F114), S4a-i = 60 (F115) — each at its bound, core-verified; the pit-arc → pipe-A → bricks passage shown to be one coupled maneuver that first-arrival gates cannot cut; seam protocol born (runbook §3). §S2…§"The coupled passage".
- 2026-08-23 s10 — **P2.5c-2 steps 1–4**: the Rust 4-2 enemy module exact on the core (F101/F102: 5,787 trials, 877k frames, 0 differences); item bumps refused; death pruning honoured; ygate bounce relaxation audited (0 violations / 1.6M checks); **S1 = 149 exactly**, core-verified (`chain_s1.bin`). `P2.5c-w42-enemies.md` §step 1b; `P2.3c-2c-main-area.md` §"S1 solved".
- 2026-08-23 s9 — **P2.3c-2c ygate**: the y-coupled position-goal bound (`heuristics::ygate`, `bfscx --goal-y`, `tools/ygate_audit.py` 1,485 checks 0 violations); pipe-B gate dropped as unprovable (H37). **P2.5c-1**: `tools/w42_enemy_sim.py` exact on all 588 WR rows — three piranha plants were missing from every earlier spec, the wrong-warp plant is slot-dependent (F99/F100).
- 2026-08-23 — **P0.11a**: the Mac is an operational overflow host (arm64 container, `tools/mac_run.sh`, `tools/mac_sync_engine.sh` with the sha guard, control gate exact; F105–F111). `P0.11-two-box.md`.
- 2026-08-22 s8 — **P0.10**: Hetzner chosen + authenticated; billing rules (powered-off boxes bill; delete, don't poweroff), sizing (F95–F98), quota 8 cores, the Server Auction route. `P0.10-cloud-sizing.md`. **P2.3c-2c session 8**: geometry F92, wall-entry mechanics F93, slack profile F94, S1 ladder → x-only bound cannot carry S1 (F95).
- 2026-08-22 s7 — **P2.3c-2**: warp-zone staged + coupled x bound 461 vs WR 476 (F89–F91, H35). **P2.3c-1**: `bfscx`/`bfscx-path` external-memory engine, `tools/replay_check.py`; 3 frames on the WR's last 12 frames of 4-2 (F88, framerule-absorbed). **P2.3b-2**: block states in the model (F84–F87). `P2.3c-engine.md`, `P2.3b-2-block-states.md`.
- 2026-08-22 s6 — **P2.3a/P2.3b**: 4-2 model (`W42Main`/`W42Warp`, `tracec`/`bfsc`), warp zone exact (F75), lift modeled + validated (F73/F81), scroll timing fixed (F77), alignment law F69, three MrWint-model bugs fixed (F70–F72); the WR's own pipe entry is 1 frame late (F79); the bottom route is a floor-level wall walk (F80). `P2.3a-w42-model.md`.
- 2026-08-22 s5 — **P1.3**: x-bound audited vs the core in 1-1 room 3 (1.9M checks, 0 violations, F68). **P2.5 scan**: WR = MrWint's enemy-free optimum on every solved segment (F66/F67) → only 4-1/4-2/8-1/8-2/8-3 have unexplored room. **P2.5a**: room-1 enemy rules validated by `tools/room1_enemy_sim.py` (F64/F65; port pending, see P2.5a/b). `P1.3-heuristic-audit.md`, `P2.5-segment-scan.md`, `P2.5a-room1-enemies.md`.
- 2026-08-21 s4 — **P3.1**: `tools/oob_audit.py` + `docs/oob-audit.md` — the H7 cells are unreachable by indexed/pointer stores; the block-buffer wrap write → H30. **P0.7**: `docs/input-semantics.md` (F62). **P2.1b-m2 part 1 / P2.1b-m / P1.2-lite**: MrWint's model built, fixed, extended with goombas, exact on ~190k frames (F53/F56–F60); H27 refuted from the stairs-top state (F57). `P1.2-lite-smb-opt.md`, `P2.1b-pole-search.md`.
- 2026-08-21 — **P0.8** `docs/prior-tools.md` (F52); **P2.1a** `src/search/bfs.c` (F47–F49); **P1.1** QuickNES harness, RAM identical to FCEUX on every WR row (F45/F46); **P0.6** `docs/warp-model.md` (F38–F44; H5/H6/H13 refuted at table level); **P0.2** WR movie + ROM verified (F1, F15–F17); **P0.9** `docs/community-claims.md` (F35–F37); **P0.5** `docs/timing-model.md` (F31–F34); **P0.4** slack table (F27–F30, `tools/slack_table.py`); **P0.3** WR syncs in FCEUX + BizHawk (F23–F26); **P0.1** tooling (F18–F22); plan/process/status scaffolding, git init.

## The 4-2 hope (standing thread — do not let this quietly die)

**The open question, stated once:** *nobody has ever measured the cheapest possible way to build the
4-2 scroll offset.* Every number we have is an upper bound from a search that wasn't trying to be cheap:
the bottom route's ~31 came from a single-key beam (the exact defect F128 documents), and the top
route's 43 was the first thing a beam found at a generous deadline (F127). The budget is 22.
The structural argument against (F123: every known mint mechanism costs Mario the speed he needs to
reach the pipe) is real and is why the prior is maybe 1-in-4 — but that same class of argument was
wrong once already today (F122 → F127). **It is a measurement, not a belief, and it has not been taken.**
Owner: P2.3c-9 Part B (roots 415/449/484/509, descending ladder, step the root back when it plateaus).
Blocked only on Part A (the entry-frame goal). Deprioritised behind 8-4 by the user 2026-08-24 s16,
explicitly *without* conceding the question.

## Needs user input

- **Does 4-2 reclaim priority from 8-4?** `docs/decisions.md` (session 14 evening) made the 8-4
  campaign the primary track *because 1-1 and 4-2 were closed*. Session 16 reopened 4-2: F122 is
  refuted, the top route provably reaches the warp's offset and enters the pipe (core-verified), and
  F123's bottom-route closure is caveated because it too came from a single-key beam. Per PROCESS
  ("don't re-litigate decisions.md; if new evidence argues for changing a decision, record it here
  and continue"), this is recorded, not acted on. Note the honest counterweight: the current top-route
  warp costs **596** frames vs the WR's 588 and the 575 one-framerule line — a 21-frame gap, and it
  does not yet warp to the right place (F129). 8-4 remains unquantized (1 frame = the record).
  Default if no answer: continue the 4-2 line only as far as P2.3c-9 (the F129 goal fix, which the
  engine needs regardless, plus its Part-B cost ladder — one bounded unit that turns "4-2 might be
  alive" into a number), then return to the 8-4 queue via **P2.2a′** (enemy-free multi-apex; the cheep port is conditional on that going dry).
  **The arithmetic that frames the decision:** 4-2 = 553 movement + key. The 575 one-framerule line
  allows a key of **22**. Every price we know is above it — bottom route ~31 (F123, itself caveated
  as single-key-beam evidence), top route **43** as found today (596 total, and that path does not
  even warp correctly yet; adding F129's zero-scroll entry makes it *more* expensive, since Mario
  must brake to a stall at x 1348). 43 is a found value, not a minimum: nobody has ever measured the
  *cheapest* mint on the top route. That measurement is P2.3c-9 Part B and it is the whole decision.

## Loose ends (small, unassigned)
- **Kept artifact:** `runs/P2.2a-prime/keep/apex_candidates_4333.bin` — the 4,333 room-3 apex states (step 162)
  from the wide diversity beam. 416 KB. This is the candidate set F133's negative rests on; keep it until H25 is
  settled proof-grade, so a later exhaustive approach can be diffed against it rather than re-derived. The 15 GB
  of surrounding layers were deleted (re-derivable via `runs/P2.2a-prime/approach2_launch.sh`).
- **Cosmetic but misleading: the beam/offset log line prints `[warp needs 132]` on EVERY case.** That number
  is 4-2's wrong-warp threshold and means nothing for `W84Room3`/`W11Room1E` — an 8-4 log now reads
  `max offset 74 [warp needs 132]`, which a fresh session could easily misread. Make the suffix case-specific
  (or drop it unless the hook is `w42_enemies`). `main.rs`, the `beam:` and `offset:` prints. Logs are the
  search record here, so this is worth a one-line fix at the next engine touch.
- **The Mac's engine is STALE (session 16 changed `tools/smb-opt-modes.patch`).** Per PROCESS/runbook §5,
  run `tools/mac_sync_engine.sh` **on the Mac** before trusting any Mac number, then the control gate
  (`bfscx W42Main data/wr/wr_inputs.bin 6584 575 587 --lift 0 --check-path 12` -> 6, 16, 34, 70, 134, 673,
  3472, 16472, 69489, 257001). `tools/mac_run.sh` refuses to run the binary until the sha stamp matches (exit 3).
- **Mac engine is STALE (session 15):** `tools/smb-opt-modes.patch` changed (W84Room3 bound fix +
  horizon 200). Before ANY Mac run: `tools/mac_sync_engine.sh`, then re-run the control gate
  (`bfscx W42Main data/wr/wr_inputs.bin 6584 575 587 --lift 0 --check-path 12` → 6, 16, 34, 70, 134,
  673, 3472, 16472, 69489, 257001). `mac_run.sh` refuses the binary on a sha mismatch (exit 3).
- **Disk — Mac (133 GiB free):** stale layer dirs under `/Users/mattwatts/code/smb/runs/P2.3c-2c/`:
  `s4w4_d62_drift_layers` 212 G, `s4w4_d62_mac_layers` 142 G, `top_s4aip_mac_layers` 46 G (the
  1130 seam — moot since the G-line). All re-derivable; an `rm -rf` over ssh is blocked for the
  agent — user: `ssh mac rm -rf /Users/mattwatts/code/smb/runs/P2.3c-2c/{s4w4_d62_drift_layers,s4w4_d62_mac_layers,top_s4aip_mac_layers}`.
- **Disk — Linux (148 G free):** `runs/P2.1b-model` 81 G (run 4's `room_layers` + the 8 slices —
  delete once F116's write-up is reviewed; the logs are the record); `runs/P2.3c-2c/*_layers`
  26 G (keep `s4v3_layers`' last file = the 509 seam until the finale is settled; the rest
  re-derivable).
- Explainer page (`docs/web/`, README has the publish-in-place URL) is behind the results —
  see the wrap-up list above.
- Row-origin note: FCEUX/BizHawk dumps and the QuickNES output use different row origins
  (F45: FCEUX row r ↔ QuickNES r−3; fm2 record j → FCEUX row j+2); any tool mixing them
  must state the offset. `tools/check_sync.py`/`compare_dumps.py` are FCEUX/BizHawk-only.

- **FORK RETIRED; 4-2 CLOSED both routes (F122 top / F123 bottom, session 14).** The follow-up
  ideas ("offset earlier?", "cheaper mint?") were tested directly with `--goal-offset`: the mint
  is speed-priced at ~30 frames on any route — no 4-2 framerule without H38's
  speed-preserving-mint hope — **which P2.3c-7 then refuted at code level (H38 done): 4-2 rests
  entirely.** **Next unit (queue head, from the user's 1-1 question + the pivot decision):
  P2.5b-1 — 1-1 room-1 H29** (deficit **1** = the cheapest framerule on the route; port the
  validated P2.5a room-1 enemy rules into the engine by adapting `w42enemies.rs`, difftest to 0,
  then the deadline-367 exhaustive search — ~5M states/layer (F82), proof-grade, no beam
  needed). Then 1-2 (~5 left on the best-known route), then 8-3 (~7 after F37). The user can
  redirect (Track B glitch hunt / H35 warp zone are the alternatives).
- **Fork MrWint's smb-opt vs the patch file?** (user question, 2026-08-24). Today the engine
  diff is `tools/smb-opt-modes.patch` (committed every unit; the clone is untracked; the Mac
  rebuilds from it with a sha guard). A private fork would give granular engine history; a
  public fork is publication (touches D4) and the natural reproducibility vehicle at
  submission. Options: patch-only / private fork now / public fork at submission.
- **Cloud quota:** Hetzner Cloud is authenticated (`hcloud` context `smb1-tas`; token in
  `~/.config/hcloud/cli.toml`, never in the repo) but the new account is capped at 8 dedicated
  cores (≈ 1.08× the laptop, F96) and the console refuses a limits request — re-request once
  the account has history. The way around it is the Server Auction (Robot; no vCPU quota,
  pro-rata hourly, F97). Decision rule F98: don't rent on spec — size from the run's frontier.
  Rules and prices: `docs/experiments/P0.10-cloud-sizing.md`. `hcloud context create` needs a
  TTY (user's terminal, or `HCLOUD_TOKEN` env) — never type a token into a `!` command.
- (optional) **Ask Hetzner support** whether sustained full load on a shared tier is
  acceptable — outreach, needs explicit go-ahead (D4); only matters if P0.10a likes them.
- (optional) **Native emulator install on the host** (`sudo dnf install -y fceux
  xorg-x11-server-Xvfb mono-core mono-devel libgdiplus lsb_release cmake clang gdb strace`)
  would let `tools/fceux_run.sh` skip the container. Convenience only.

## Key numbers (current headline numbers; each reproducible by a script in tools/ — per-unit numbers live in the experiment files)
| Quantity | Value | Source / script |
|---|---|---|
| WR movie length / last input | 17,868 frames (4:57.31); last input frame 17848 (0-based), 19-frame coast to the axe on 17867 | `tools/fm2_info.py`, `tools/check_sync.py` (V) |
| WR first Start / L+R use | Start on frame 41 (rows 34–43 equivalent, F31); 85 L+R frames, 0 U+D | `tools/fm2_info.py [--list-lr]` (V) |
| Framerule | 21 frames; RTA-equivalent 4:54.032; no-L+R TAS 4:54.265 (14 frames slower) | S |
| WR level-entry frames (fm2, 0-based) | 1-1 42, 1-2 1944, 4-1 3766, 4-2 6042, 8-1 7723, 8-2 10813, 8-3 12956, 8-4 15057 | `tools/check_sync.py` (rows −1) (V) |
| Per-level slack/deficit (frames) | 1-1 20/**1** (closed end to end, F116 + F124), 1-2 13/8 (5 on Maru's route, S), 4-1 12/9, 4-2 8/13 (10 after F88; top route in the model: two framerules minus the warp key, F118/F120), 8-1 3/18, 8-2 2/19, 8-3 11/10 (FPG+242: 7, S), 8-4 unquantized | `tools/slack_table.py data/wr/fceux_wr.ram` (V) |
| Per-level frames (load→next load) / lag | 1-1 1902, 1-2 1870, 4-1 2228, 4-2 1729, 8-1 3042, 8-2 2143, 8-3 2101, 8-4 2810 (+43 boot/title); 24 lag frames, none in-level | `tools/slack_table.py`, `tools/check_sync.py` (V) |
| **4-2 main area, top route (enemy-aware, vine-bumped)** | **553** = 149+184+82+34+35+25+44, every segment at its movement bound; x-only floor 552; QuickNES 553/553, 0 mismatches, 2 stomps, entry GES 3 at record 7136; FCEUX main area 552/552 identical, entry Δ 35 rows — wrong warp diverges (scroll) | `runs/P2.3c-2c/chain_s4v4.bin`, `w42_553.fm2`; `tools/replay_check.py --case W42Main --first 6584 --prefix 0 --path runs/P2.3c-2c/s4v4_seg553.bin --enemies 0 --down` (V) |
| 4-2 wrong-warp finale from the 509 chain (scroll-constrained, drift bound) | d ≤ 58: proof-grade dry (frontier 130M → 0 by layer 48); d62: 329M at layer 38 ×1.35/layer, cap-killed; d66: 143M at layer 30 ×1.2/layer, stopped — both null | `runs/P2.3c-2c/s4w4_d58_drift.log`, `s4w4_d66_drift.log`; Mac `runs/P2.3c-2c/s4w4_d62_drift_mac.log` (pre-drift rungs: `s4w4_entry_d58big.log`, Mac `s4w4_entry_d62_mac.log`) (V) |
| Drift-bound validation (F121) | control gate byte-identical drift-off; WR warp survives `--check-path` 0 violations drift-on, 32,472 wrong-scroll entries pruned; audit 400 traj + WR, 211,675 pairs, 0 violations | `tools/drift_audit.py`; `runs/P2.3c-2c/s4w4_d58_drift.log` (V) |
| 4-2 enemy module vs core (F102) / vs WR dump | 5,787 trials, 877,058 frames, **0 differences** (1,825 deaths, 3,686 stomps, 949 kicks); dump oracle 0 mismatching rows / 586 incl. the vine | `tools/model_difftest.py --case W42Main --first 6584 --enemies 0 --prefix-dir runs/P2.5c/prefixes/… --require-event`; `tools/w42_enemy_check.py` (V) |
| 4-2 model vs core (player, lift, block states) | warp zone 0 differences (WR 476 frames + 40×300 random + 40×480 mutated); main area 0 differences (WR 587 frames, 100 random, 240 mutated block-bumping) | `tools/model_difftest.py --case W42Warp --first 7247 …` / `--case W42Main --first 6584 --lift 0 …`; `tools/block_state_check.py` (V) |
| 4-2 control gate (both boxes, after every engine change) | `bfscx W42Main data/wr/wr_inputs.bin 6584 575 587 --lift 0 --check-path 12` → layers 6, 16, 34, 70, 134, 673, 3472, 16472, 69489, 257001; goal at layer 10 | `runs/P2.3c/ctrl_w42main_p575_d587.log` (V) |
| 4-2 warp zone | enemy-free coupled bound **461** at the WR's entry vs WR 476; return from the WR's drop state optimal (76); frontier ×1.25/layer at 15 frames of slack | `runs/P2.3c/warp_stage3_p0_d475.log`, `warp_stage_p400_d7{5,6}.log` (V) |
| 4-2 frames on the WR's own route | 3 on the last 12 frames before the wrong-warp pipe (F79 + F88), framerule-absorbed (deficit 13 → 10); other pipe entries earliest-possible | `tools/replay_check.py … --path runs/P2.3c/ctrl_w42main_path.bin --lift 0 --down`; `tools/pipe_entry_scan.py` (V) |
| **1-1 room 1, enemy-aware exhaustive (F124)** | optimum **368** = the WR's; d367 dry in 4.7 s (root bound 367, frontier 1→36, extinct at layer 21); reference path → GOAL at step 368 with 0 bound violations; the single lost frame is at step 21 | `runs/P2.5b/w11_d367.log`, `runs/P2.5b/w11_d368.log`; `bfscx W11Room1E data/wr/wr_inputs.bin 196 0 367 --enemies 0 --threads 8` (V) |
| 1-1 third room, whole-room exact search (run 4, F116) | relaxed model + goombas, deadline 238: no FPG grab ≤ 238; peak frontier ~693M/layer; 660.6M states in a 24-px window at the stairs top | `runs/P2.1b-model/room_compact_d238*.log`, `fpg_part*.log` (V) |
| 1-1 model vs core | 0 differences: player-only 1,600 trials; with goombas 97,335 frames / 700 trials, 119 deaths, 37 grabs | `tools/model_difftest.py [--goombas --root-record 1048] …` (V) |
| Bound audits | x-bound (room 3): 1,906,600 checks, 0 violations (F68); ygate (S1 goal): 1,485 checks, 0 violations; bounce band ~1.6M checks, 0 violations | `tools/heuristic_audit.py`, `tools/ygate_audit.py` (V) |
| WR vs MrWint segment optima | gap 0 on all 10 solved segments (1-1 ×4, 1-2 opening, 8-4 ×5); 8-4 at the speed cap outside 2 accelerations (F66/F67) | `docs/experiments/P2.5-segment-scan.md` (V) |
| Stage-1 core | 15.0k fps/instance, 104k fps on 12 threads; state 12,792 B, save+load 2.5 µs (F46) | `tools/build_core.sh`, `./build/harness …` (V) |
| Emulator alignment | FCEUX row r ↔ QuickNES row r−3; fm2 record j → FCEUX row j+2 / QuickNES frame j−2 (F45) | `tools/compare_ram.py … --offset -3` (V) |
| Reachable warp destinations | 1-2 → {4,3,2}/{−1,5,−1}; 4-2 ceiling → 5; 4-2 $2F → {8,7,6}; WZC ∈ {0,1,4,5,6} | `tools/warp_tables.py`, `docs/warp-model.md` §5.4 (V) |
| Throughput (for sizing) | laptop 8.75M generated states/s at 12 threads (bfs11cr); Mac ≈ 0.84× per thread in-container (rough, P0.11 §7 #10); Hetzner 8 dedicated cores ≈ 1.08× the laptop (F96) | run-4 logs; `P0.10-cloud-sizing.md` (V) |

## Spend
Cloud total: **$0 / $300 cap.** Hetzner Cloud, context `smb1-tas`; no resources exist
(`hcloud server list` / `volume list` / `primary-ip list` empty, 2026-08-22). Rules (delete, never
poweroff; hourly rounded up; check `hcloud server list` every session; auction boxes bill
pro-rata by the hour): `docs/experiments/P0.10-cloud-sizing.md` §rules, F95/F97. Record each
spend here as it happens.

## Model omissions (keep current — the cracks are most likely here)
Mechanics the smb-opt player model does not contain, or contains unvalidated. Every refutation must say which of these could matter in its room and why not.
| mechanic | status | where on the route | risk to bounds |
|---|---|---|---|
| enemies: stomps/bounces | 1-1 rooms 1 (sim) and 3 (validated); **4-2 main modeled + validated on the core (F102)**; the ygate bound admits stomp bounces under `--enemies` (bounce band, audited) | everywhere | bounces change y only (sound for x) |
| enemies: koopa shells (kick, carry, chain) | 4-2 main modeled + validated (F102: 949 kicks); other levels not | 4-1, 4-2, 8-1…8-3 | no x effect on Mario; kills/deaths only |
| piranha plants / enemy slots | 4-2 modeled incl. parser-driven spawn and slot occupancy (F99/F100); slot-dependent plants are route properties | any pipe level | a free slot at a render frame spawns a plant in a pipe Mario must enter |
| moving platforms / lifts | 4-2 lift modeled + validated (F73/F81); 8-x lifts not yet (same code path) | 4-2, 8-x | vertical lifts do not move x (F68); horizontal ones (8-x) would |
| block states after a bump | modeled + validated for 4-2 main (`Options::BlockStates`, F84–F87); other cases need their cell lists + start phases | any level with bricks on the route | a bumped hidden block becomes a platform; a $23 cell stops a wall walk (F80) |
| spawned items | **vine (64,3) modeled + validated (session 12: `CLASS_VINE`, slot injection, F119)**; mushroom (28,7)/(55,7) and star (81,7) still refused under `--enemies` (H34) — big Mario / star not modeled | 4-2 main; any level with item blocks | only matters if a faster route needs the item; refusing may exclude slot-filling bumps |
| screen scroll / offset latch | modeled (`WithScrollPos`, F77); **the collision-minted scroll offset is understood (F120) and bounded (drift bound, F121)** but only the 4-2 finale's case goal enforces it | everywhere; load-bearing for the 4-2 wrong warp | any goal that depends on ScreenLeft/parser state must pin it (the 553 lesson) |
| head/brick bumps, coin/powerup blocks | fixed + difftested (F70/F72/F84) | 1-1 room 1, 4-2, 8-x | none for x; y paths and landing frames |
| joypad above/below the screen | fixed: disabled only in water areas (F71) | 4-2 warp zone, 8-4 water | — |
| Down / pipe entry | entry = "possible" (Down not an input); add Down when replaying (F74) | every pipe | — |
| RNG-driven enemies (Hammer Bros, Bowser, fire) | not modeled — RNG is outside the model by design | 8-3, 8-4 | an 8-3/8-4 search must partition RNG-free segments or carry the LFSR |
| swimming | modeled by MrWint, unvalidated by us | 8-4 water room | unknown until difftested |
| springs, vine climbing, big Mario, fire | not modeled | not on the route | — |
| lag frames, game timer | outside the model by design; `docs/timing-model.md` | — | — |
