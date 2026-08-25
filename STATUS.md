# STATUS — SMB1 TAS project

This file is the current state only. The story is in `docs/log.md` (one entry per session)
and `docs/experiments/`; standing search rules are in `docs/search-runbook.md`; the
pre-cleanup narrative version of this file is archived at
`docs/archive/STATUS-2026-08-24-pre-cleanup.md`. Keep every section here short.

**Updated:** 2026-08-24 (session 16 — P2.3c-8 done: the beam was a per-layer seam; F122 refuted, 4-2 top route REOPENED; no search running)

## Where we are
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
- **[TRACK A, session 17] RUNNING — the P2.2f d267 beam CONTROL** (detached, `pgrep -x smb-opt`).
  `bfscx W84Room2 data/wr/wr_inputs.bin 15917 0 267 --enemies 0 --beam 3000 --beam-buckets off,y,spd,sub
  --beam-max 600000 --layer-dir runs/P2.2f/d267_layers --threads 5` under
  `systemd-run --user --scope -p MemoryMax=7G -p MemorySwapMax=0`. Log `runs/P2.2f/d267_ygate_w3000.log`.
  ~8.5 s/layer, ~480k records/layer ⇒ ≈ 40 min and ≈ 8-10 GB of layer files (145 G free at launch).
  **How to read it:** `grep -E "goal reached|no goal|^total " runs/P2.2f/d267_ygate_w3000.log`.
  A **goal at layer 267** = the machinery is validated and d266 is the next run (change 267 → 266).
  **No goal** = still under-powered, and the next lever is an ENEMY axis in the bucket key (H40), NOT more
  width — narrower runs at width 50 / 200 / 2000 already failed (F137). Either way **delete the layer dir**
  unless a d266 run follows immediately.
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
- **P2.2f — H42: dissolve MrWint's 8-4 room-2 seams (declared 2026-08-24 s16; port DONE s17).**
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
  **THE SEARCH IS THE REMAINING STEP, and its bound had to be rebuilt first (F137).** The x-only table is
  satisfied **at floor level ~15 frames before the goal**, so h = 0 across the whole climb and a bucketed
  beam finds no goal even at the WR's own deadline 267 (width 50: no goal; width 2000 / ~300k per layer:
  no goal, frontier races past to x 2471). Added a y-coupled `YGate` bound over the goal's own NECESSARY
  condition `x >= 2436 && Player_Y <= 64` (`W84R2_PIPE_Y`), joined with the x table. Trap recorded:
  `YGate::steps_xy` scans from k = 1 so it never returns 0 and prunes the WR's own goal — states already
  satisfying the condition are given h = 0 explicitly. Audits clean: 0 bound violations on the WR line,
  and `ygate_audit --mutate` = **1335 checks, 0 violations, min slack 0**.
  **PRE-REGISTERED READING (do not skip): the d266 run is meaningless until the d267 CONTROL FINDS A GOAL.**
  A beam that cannot reproduce the WR's own 267 says nothing about 266. Width 200 with the new bound went
  extinct at layer 264, 7 px short (max x 2429) — too narrow at the end, not a verdict.
  **NEXT: (1) read the running d267 control (Running jobs); (2) if it still finds no goal, the bucket key
  has no ENEMY axis — H40 asks for beetle x/state, plant phase, paratroopa phase and slot occupancy, so add
  an ext-derived axis to `--beam-buckets`; (3) only then d266, and core-replay any goal (runbook §4).**
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

**Priority (decisions.md 2026-08-24, session 14 evening): THE 8-4 CAMPAIGN IS THE PRIMARY
TRACK.** 8-4 is unquantized — one frame = the record; an earlier last input (longer ending
coast, F17) also wins. Order: H25 turnaround stop → H1 ending coast → water room (no solved
optimum) → transitions/wrong-warp scroll (the 4-2 specialty) → Bowser/RNG. One Track B unit
(P3.2 oracle) interleaved every few sessions. Framerule levels (P2.3e) demoted to third.
1-1 and 4-2 are closed. Big single runs → cloud; segments run locally (unchanged).

| ID | Title | Track | Size | Depends on | Acceptance |
|---|---|---|---|---|---|
| P2.3c-9 | **F131 — model the wrong-warp ENTRY FRAME, then ladder the top-route warp cost.** Part A (was 'small', is not): the warp needs the entry frame's latched `Player_X_Scroll` to be 0 (F129), but that frame is one the search does not simulate — the model's goal fires when Mario *reaches* the entry x (the WR's own goal step has d = 2), so a goal-side `SL + 48*d <= 1216` test **rejects the WR's own warp** (F131, verified). The fix is case-level: make the goal fire on the entry frame under Down (or carry one extra simulated step), not a refusal tweak. The sound necessary condition `screen_left16 >= 1217` is what ships today, so **the search still emits candidates that do not warp** — the core-replay destination check (runbook §4.3) is the gate. **Part B — the exact shape of the search (do NOT run a whole-level pass; F132 proved that fails).** Root on the known 553 chain at one of the G-line cumulative points — the G-line is 149+184+82+34+35+25+44, so the roots are prefixes **415 / 449 / 484 / 509** (= 138 / 104 / 69 / 44 frames from the pipe). Horizon = (553 − prefix) + slack, laddered **downward** until dry: from 509 that is d87 (the F127 result) → d84 → d80 → d76 → d72; if the ladder bottoms out above 22 frames of key cost, step the root back to 484 and repeat, because a cheaper mint may need a different *arrival* state at the wall and a fixed root pre-commits it (the seam problem one level up — F123's ops lesson was already "root ≥ step 200"). Short horizon (tens of layers) is what lets the bucketed beam be wide enough to matter, and it is the same shape as P2.3c-11a. Every goal core-replayed + destination-checked. | A | M–L | — | Part A: the reference-path audit still marks the WR's warp GOAL **and** a d>0 entry is refused; beam-off gate byte-identical. Part B: a measured minimum top-route key cost vs the 22 the 575 line allows, with the root stepped back until the number stops improving |
| P2.3c-10 | **Re-audit every beam-derived verdict with `--beam-buckets` (F128).** Any conclusion resting on "the search never found X" was produced by a single-key beam. First: **F123's bottom-route mint economics** (`mint_cost_beam.log`, 2M offset-first) — its 27-frame minimum mint and the 584-585 floor gate the whole "4-2 closed both ways" claim. Then the F122 table's remaining rows. | A | M | P2.3c-9 | Per-verdict: the bucketed rerun's number vs the original, and an explicit statement of which conclusions survive |
| P2.2a′ | **8-4 room 3: the multi-apex seam, ENEMY-FREE FIRST (the real next 8-4 unit).** F125 proved the return leg optimal *from the WR's apex* (h = 33 = WR, the 32-rung dry at layer 1), so H25's frame can only be in **reaching a different apex state** — which an approach search goaled on the WR's apex deletes by construction (H39's seam corollary). Search the 162-frame approach with **generic** buckets (mechanism unknown ⇒ discovery keys, H40) including an apex-band axis, emit a **set** of apex-region states, and compute the return cost for each. Run it **enemy-free** and let the core adjudicate the plants/cheeps per candidate (the F126 cheapest-order note, line 117): one core replay checks one path exactly, which is far cheaper than modelling the frenzy up front. | A | M | — | A set of ≥1 non-WR apex states with per-apex return costs; either a 32-frame return from one of them (= the H25 frame, then the record pipeline) or a dry across the whole set |
| P2.2f | **H42 — dissolve MrWint's 8-4 room-2 seams (NEXT UNIT; highest-prior untested spot on the route).** **Build a `W84Room2` case first** — MrWint ships only the two halves (`W84Part2Speedup`, `W84Part2VertPipeEntry` in `w84.rs`); a case spanning control → pipe clip has to be written the way `W84Room3` was (block map, goal, overshoot bound), then WR-line-exact + a random battery before any search. Prior raised by the H42 sub-check: room 2's middle **contains four enemy objects** (two Buzzy Beetles at x 2048/2080, two id-$0e at x 2224/2256) and the clip seam at **x 2373 sits exactly between that group and the next pair at 2480/2512** — i.e. an enemy-avoidance boundary, which is precisely where generate-and-test buys coverage nobody has had. F66's table decomposes room 2 into `W84Part2Speedup` (control → x ≥ 1981, 70 frames), a **157-frame middle at the speed cap**, and `W84Part2VertPipeEntry` (**x 2373** → pipe clip, 40 frames) — rows 15918→16185, 267 frames total. The WR equals each piece, so it is provably no better than that decomposition; and `P2.5-segment-scan.md` records the clip's start as a **hand-picked mid-air state**, the lossiest kind of seam. Search control → pipe clip as ONE span with a diversity beam, deadline 266 (= one better than the WR), then core-replay any improvement. 8-4 is unquantized, so **one frame is the record** (H24). | A | M | — | Either a ≤266-frame room 2 core-replayed (→ runbook §4 pipeline) or a documented dry with the beam width and bucket key stated |
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

Wrap-up items (fold into whichever unit touches them first): audit the truncated goal-parent
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
