# Input semantics of SMB1 (P0.7) — what every button does, from the code

Source: `data/disasm/smbdis.asm` (line numbers below). Verified against the validated player model where
noted (F56). Bit layout of `SavedJoypadBits` ($06FC): A=$80 B=$40 Select=$20 Start=$10 Up=$08 Down=$04
Left=$02 Right=$01 (our NES-order input files use the reversed layout, see `tools/fm2_to_inputs.py`).

## 1. Reading (`ReadJoypads`, 2421–2447)
- All 8 bits are read every NMI; **no masking of Left+Right or Up+Down** — the game sees both.
- **Select and Start are edge-triggered**: if the previous frame's `JoypadBitMask` already had the bit, the
  saved bits are stored without Select/Start ($CF mask). A held Start cannot re-pause; a fresh press is
  needed (the 43-frame `GamePauseTimer` below gates it as well).
- `PlayerCtrlRoutine` (5558) splits the bits into `A_B_Buttons` ($0A), `Up_Down_Buttons` ($0B),
  `Left_Right_Buttons` ($0C). In **water areas** (AreaType 0) the bits are nulled when Mario is outside the
  vertical play area (Y high ≠ 1 or Y ≥ $D0). During death (GES $0B) the bits are not loaded.
- `AutoControlPlayer` (5555) overrides the bits with a constant for entrances, the flagpole slide (Down,
  5820), the end-of-level walk (Right), pipe intros (Right), vine exits.

## 2. Left / Right
- Ground (`OnGroundStateSub` 5903): `PlayerFacingDir := Left_Right_Buttons` whenever non-zero — so
  **L+R sets facing = 3**, a value no single button produces. `GetPlayerAnimSpeed` (6195) compares the L/R
  bits with `Player_MovingDir` (1 or 2): with L+R they never match → `ProcSkid`: if |speed| < $0B the
  speed and `Player_X_MoveForce` are zeroed and moving dir := facing (3!); `RunningSpeed` is not cleared.
- `X_Physics` (6139): the run cap needs `Left_Right_Buttons == Player_MovingDir` → **L+R on the ground
  never runs** (walk cap $18 with friction $98/$D0), unless airborne with |speed| ≥ $19 (run physics
  regardless of buttons). Friction adder is **doubled when `PlayerFacingDir ≠ Player_MovingDir`**
  (6180–6190; F48) — L+R (facing 3) always doubles it, the key to the WR's 0→40 in 33 frames (F47).
- `ImposeFriction` (6227): `Left_Right_Buttons & Player_CollisionBits`; if any bit: `lsr` → carry = Right →
  accelerate right (`LeftFrict` path, despite the label); else Left → accelerate left. **With L+R, Right
  wins** (the direction of acceleration); if neither bit survives the collision mask, the current speed
  decays toward 0. The cap is `MaximumRight/LeftSpeed` with the subpixel carry kept.
- Air (`LRAir` 5947): friction is imposed only while L or R is held (speed is otherwise constant in the air);
  L+R → accelerate right with the doubled adder if facing ≠ moving.
- Climbing (`ClimbingSub` 5966): L/R (masked by the collision bits) jumps off the vine/pole sideways once
  per `ClimbSideTimer` ($18 frames): X += `ClimbAdderLow/High` (±$0E/$04 with page carry) and **facing :=
  inverted L/R bits** (L+R → facing 0).
- **Facing 3 and facing 0 are out-of-range indices, and `PutPlayerOnVine` indexes two 2-byte tables with
  them (F268/F269/F270, `docs/experiments/H12-input-semantics.md`).** `SetVXPl` (12219) does
  `ldy PlayerFacingDir / adc ClimbXPosAdder-1,y` and, when the grabbed cell is buffer-1 column 0
  (`$06 == 0`), `adc ClimbPLocAdder-1,y` onto `ScreenRight_PageLoc`. ROM $DE25 `f9 07` / $DE27 `ff 00` /
  $DE29 `18 22 50 68 90`, so facing 3 reads **$ff** and **$18** (+24 pages, measured: x 3063 → 9471) and
  facing 0 reads **$8a** and **$07** (measured in-page: x 583 → 714). The flagpole path forces facing = 1
  first; the vine path does not.
- Side scroll: `Player_X_Scroll` = horizontal movement; `ScrollHandler` only scrolls right (F48 model).
- **The screen clamps the player every frame (`ChkPOffscr`/`KeepOnscr` 5428, F269/F270).** If
  `GetXOffscreenBits` reports d7 the player is snapped to `ScreenLeft`, if d5 to `ScreenRight − 16`; a
  page-scale teleport always reports d7 and so is undone. The furthest right the game allows is
  `ScreenRight_X_Pos − 16`, and **the WR runs a median 127 px behind it in every level** — about 50 frames
  of headroom, which is the ceiling for any displacement mechanism (H47).

## 3. Up / Down
- Down on the ground with L or R held (5576–5586): **nullifies L/R and U/D for this frame** — for small
  Mario this equals "no direction" (friction decays; facing unchanged); for big Mario it also crouches
  (`CrouchingFlag`, 5874–5882; bounding-box control 2; no crouch-walk).
- Down in the air: nothing. Up outside climbing: nothing (no "look up").
- Climbing (`ProcClimb` 6048–6062): `Up_Down_Buttons & Player_CollisionBits`: none → stay; Up (or U+D —
  **Up wins**) → Y speed −1 with force $20; Down → +1 with force $FF (≈ 2 px/frame). `FlagpoleSlide` forces
  Down while Y < $9E (F55).
- `PlayerBGCollision`/`HandleClimbing` (12153): grabbing a vine/pole does not read the buttons.

## 4. A / B
- Jump (`CheckForJumping` 6064): needs A pressed **and not pressed on the previous frame**
  (`PreviousA_B_Buttons`, saved every frame at `SaveAB` 5356). Mid-air A is ignored except swimming
  (`ProcJumping`). Jump velocity/forces by `Player_XSpeedAbsolute` (6084–6130): < $10 → −4 (walking), ≥ $10
  → −4/$1E, ≥ $19 → −5 (running, forces $28/$90). **`Player_XSpeedAbsolute` is updated only in
  `ImposeFriction`** (i.e. on frames with L/R held or with speed decay), so the jump type can lag the true
  speed (used by the WR at the pole: F60).
- Holding A during the rise (`JumpSwimSub` 5922): while rising and (A held since the jump start) or still
  within `DiffToHaltJump` of the origin, the lighter `VerticalForce` applies; otherwise `VerticalForceDown`
  (full gravity). Release A early → shorter jump.
- B: run (`X_Physics`: with L/R == moving dir; sets `RunningTimer` = 10 so the run cap persists 10 frames
  after release, F56); fireballs for Fire Mario (edge-triggered via `PreviousA_B_Buttons`, 6286).
- Swimming: A = stroke (`JumpSwimTimer`). **NOT covered here, and the stated reason was wrong: the route
  DOES swim.** 8-4's water room is 696 route frames, 667 of them at the swim cap (F265 sub-area `r4`,
  P2.5 §"8-4 speed profile"). The input semantics of the one place the route swims are unread — open in
  H12 (`docs/experiments/H12-input-semantics.md` §6).

## 5. Start / Select / pause (NMI 780–800, `PauseRoutine` 851–882)
- Start (fresh press, game mode, task 3): toggles `GamePauseStatus` d0 and sets `GamePauseTimer` = $2B;
  while that timer counts (43 frames) Start is ignored → **a pause lasts ≥ 44 frames** (press, 43, unpress
  edge). Select does nothing in play (only the title menu: player count / world select with B).
- While paused the NMI skips: `TimerControl`/`DecTimers` (all frame **and** interval timers, i.e. the
  framerule clock `IntervalTimerControl`), `inc FrameCounter`, sprite handling and `OperModeExecutionTree`
  (all game logic). **It does not skip the LFSR step** (`PauseSkip` → `RotPRandomBit` 801–812): the
  `PseudoRandomBitReg` advances every NMI, paused or not. So a pause shifts the RNG by ≥ 44 steps relative
  to all game timers and the frame counter parity — a lever for RNG-dependent objects (Bowser, Hammer Bros,
  Lakitu spawns, fireworks are timer-based not RNG) at a cost of ≥ 44 movie frames (the level timer and
  framerule do not advance, so the cost is purely real-time frames).
- `TimerControl` ($0747): when non-zero the NMI decrements it and skips `DecTimers` (frame + interval
  timers) but **still increments `FrameCounter`** and steps the LFSR. Set to $FF by `ForceInjury`/`KillPlayer`
  (5424–5428: injury/size change/death), cleared at pipe/area transitions (2996, 5774). So injuries halt
  the framerule clock relative to the frame counter (H3) — only relevant if damage-boosting is ever
  considered (big Mario not on the WR route).

## 6. Consequences for the search
- Inputs that matter per frame: A (edge), B, L, R, and Down only for big Mario or as a "cancel L/R"
  (equivalent to releasing L/R for small Mario). Up only while climbing. Start = pause (≥ 44 frames, RNG
  only). So the 16 A/B/L/R combinations used by `bfs11`/`bfs_par` are complete for small Mario on land.
- L+R is not a "trick input" but a normal state: facing 3 doubles the friction adder every frame until a
  single direction is pressed — exactly the WR's acceleration technique; the model reproduces it (F56).
- Held A never jumps; `Player_XSpeedAbsolute` staleness decides the jump velocity — both modelled (F56).
