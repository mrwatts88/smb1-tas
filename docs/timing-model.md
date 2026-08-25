# SMB1 timing model (P0.5) — what determines each frame count, from the code

All addresses/labels are from `data/disasm/smbdis.asm` (doppelganger). All numbers are
verified against the WR dump (`data/wr/fceux_wr.ram`, row i = fm2 frame i−1; scripts:
`tools/slack_table.py`, `docs/experiments/P0.4-slack-table.md`). The model reproduces every
number in facts F27–F29 and the ones added here (F31–F34).

## 1. The frame: NMI does everything
`NonMaskableInterrupt`: disable NMI (mirror), PPU/OAM DMA, `UpdateScreen` (VRAM buffer),
`SoundEngine`, `ReadJoypads`, then `PauseRoutine`/timers (`DecTimers`), the RNG step,
sprite-0 wait, scroll, then `OperModeExecutionTree` (all game logic), re-enable NMI, `rti`.
The main thread is an endless loop. Consequences:
- A **lag frame** (FCEUX/BizHawk: no joypad read) is a frame whose vblank arrived while the
  previous NMI handler was still running (NMI re-enable happens at its end). No timer, RNG or
  logic runs on a lag frame — the ITC phase is simply delayed by one frame.
- In the WR all 24 lag frames are boot (7) and exactly one per area load at load+2 (**17**).
  **CORRECTED 2026-08-25 (F264): the overrunning routine is `InitializeArea`/`InitializeMemory`,
  NOT `InitScreen`/`InitializeNameTables`.** The RAM clear is 1,868 bytes at 18 cycles each
  (~33,370) plus ~2,000 of NMI prologue against an NTSC frame's 29,780 — 119 %, so exactly one
  NMI is lost and never two. `InitScreen` fits at ~21,500. **Irreducible** (overrun ~5,600
  cycles; the only parameter can save 1,368) — H2 refuted, `docs/experiments/H2-lag-frames.md`. None depends on input.
  (Argument, not yet a proof that a load frame can never be made shorter — H2 stays parked.)
- Input read this frame acts this frame (`SavedJoypadBits` used by the logic later in the NMI).

## 2. Timers (`DecTimers`)
- `TimerControl` ($0747) ≠ 0 freezes all timers (used by injury/size-change routines).
- Every frame: `IntervalTimerControl` ($077F) decrements; frame timers $0780–$0794 decrement.
- When ITC underflows it is reset to **20** and the **interval timers $0795–$07A3** decrement
  too — a 21-frame period. ITC is never reset by area loads (`InitializeArea` clears only
  $0780–$07A1), so the framerule phase runs continuously from power-on (the only things that
  move it are lag frames and `TimerControl` freezes).
- Then `FrameCounter` ($09) increments and the 7-byte LFSR `PseudoRandomBitReg` ($07A7–AD)
  is stepped once (every non-lag, non-frozen frame; also during pause? — `PauseSkip` is after
  the RNG step only for the timer part; verify in P0.7).

## 3. Boot and the Start press
Power-on → 7 boot lag frames → title screen: `OperMode_Task` 0 `InitializeGame`, 1
`ScreenRoutines` (title drawn, rows 9–32), 2 `PrimaryGameSetup`, 3 `GameMenuRoutine` from row 34.
Start (alone, or A+Start = continue) → `ChkContinue` → `OperMode` = 1 the same frame, load
row L = the Start row. Then the level-start law (§5) gives control at L + 154 + w. Because w
depends on the ITC phase at L, **any Start row from 34 to 43 gives control on row 197** (u runs
16→7, w 9→0). The WR presses Start on the last such row (43). Earlier control would need a
different boot ITC phase, which only the boot lag frames set. (H19: confirmed for this boot.)

## 4. Area loads (`NextArea`/`ChgAreaMode` → `OperMode_Task` = 0)
Row L: task 0 `InitializeArea` (clears $0000–$074B… and timers $0780–$07A1, sets
`ColumnSets` = 11, `DisableScreenFlag`); L+1: `ScreenRoutineTask` reset; L+2: task 1 and the
lag frame; then `ScreenRoutines` tasks one per frame:
0 `InitScreen`, 1 `SetupIntermediate`, 2/3 status lines, 4 `DisplayTimeUp`,
5 `ResetSpritesAndScreenTimer` (ScreenTimer is 0 after the clear → passes at once),
6 `DisplayIntermediate` (only if `AltEntranceControl` = 0: draws "WORLD x-y", **sets
ScreenTimer = 7 on row L+8**, re-enables the screen), 7 `ResetSpritesAndScreenTimer` (waits for
ScreenTimer = 0, sets it to 7 again — not waited on), 8 `AreaParserTaskControl` (renders 12
column sets, one per frame), 9–11 palettes, 12 → task 2 `SecondaryGameSetup` (1 frame), task 3
`GameCoreRoutine` with `GameEngineSubroutine` 7 `PlayerEntrance` (2 frames) → 8 control.
`ScreenTimer` is an interval timer: written on L+8 with post-frame ITC = w it reaches 0 on
L+8+(w+1)+6×21. Hence **control = L + 154 + w, w = (u − 7) mod 21** (u = ITC at L).
Checked exact on all six main entries (1-1 u=7→154; 4-1 u=20→167; 8-1 u=15→162; 8-2/8-3/8-4
u=19→166).
- Flag levels always load on u = 19 (expiry + 1) → 166.
- **Sub-area loads** (AltEntranceControl ≠ 0 or `DisableIntermediate`): task 6 is skipped,
  no wait: task 3 at L+25; side entry (Alt 1) control at L+43; vertical pipe exit (Alt 2:
  `EntrMode2` rises Mario 1 px/frame to Y < $91) control at L+122. The 4-2 wrong-warp
  re-entry (row 7221, Alt 1) is L+27. The intro→main loads of 1-2/4-2 (Alt 0 but
  `DisableIntermediate` set by `IntroEntr`) are L+43. **None of these is quantized.**

## 5. Level starts and the game timer
`Entrance_GameTimerSetup` loads the timer from the header as 401; `RunGameTimer` (called every
control frame from `GameCoreRoutine`, only when `GameEngineSubroutine` ≥ 8, not dying, not
below the screen) decrements a digit whenever `GameTimerCtrlTimer` ($0787, frame timer) is 0
and resets it to 24. The timer was cleared by the load, so the first tick is on the first
control frame (401→400) and then every 24 control-eligible frames; pipe entries/exits and
sub-area loads pause it (GES < 8). The displayed timer at the flag is therefore a function of
the control frames spent in the level: T = 400 − floor(frames_eligible / 24).

## 6. Flagpole levels: from the grab to the next load
`HandleClimbing` (player BG collision): when Mario's feet are within the thin part of a
climbable metatile (low nybble of X in [6, 10)) and the metatile is $24 (ball) or $25 (shaft),
`FlagpoleCollision`: face right, `ScrollLock`, kill Bullet Bills, silence, record
`FlagpoleScore` from Y (`FlagpoleYPosData` $18/$22/$50/$68/$90 → 5000/2000/800/400/100),
**GES = 4** (`FlagpoleSlide`), state = climbing. Same frame, later in `GameCoreRoutine`,
`FlagpoleRoutine`: if GES = 4 and climbing: if the flag object Y ≥ $AA **or Mario Y ≥ $A2
(162)** → award score, **GES = 5** at once; otherwise lower the flag 1 px/frame (the slide).
- **Flagpole glitch** = touching the pole with Y ≥ 162: zero slide frames (1-1, 4-1, 8-1, 8-2 in
  the WR, Y = 164/165). A normal grab slides 2 px/frame until Mario's Y ≥ $A2 or the flag
  object's Y ≥ $AA (8-3: grab at Y = 17, slide + walk = 173 frames; the slide/walk split and
  the slide-length-vs-height law are left to P2.x, which needs them only if a non-glitch grab
  is ever considered).
- `PlayerEndLevel` (GES 5): auto-walk right (`AutoControlPlayer` with Right only); when Y ≥ $AE
  the win music is queued; when `Player_CollisionBits` bit 0 clears (Mario behind the castle
  door), `StarFlagTaskControl` = 1. **Glitch grab → castle entry = 126 frames** in 1-1, 4-1,
  8-1 (identical small-castle layouts: pole at X=89, door trigger 105 px right); 8-3 has the
  large castle (longer walk); 8-2's glitch happens at the door (1 frame).
- Star-flag object tasks (`RunStarFlagObj`, run from the enemy loop every frame):
  1 `GameTimerFireworks` (fireworks count from the timer's last digit: 1→ y=5? (6 fw), 3→3,
  6→0… as coded: digit 1 → 5 state, 3 → 3, 6 → 0 — i.e. fireworks only for digits 1/3/6;
  `FireworksCounter` = $FF otherwise) — completes in the same frame;
  2 `AwardGameTimerPoints`: **one timer unit per frame** (+1 frame to notice zero):
  countdown = T + 1 frames (370 → 371 etc.);
  3 `RaiseFlagSetoffFWorks`: flag up 1 px/frame until Y < $72 (**32 frames** in every level), with
  fireworks queued during it if any; then `EnemyIntervalTimer[slot]` = 6 → task 4 (T_set);
  4 `DelayToAreaEnd`: waits for that interval timer = 0 and `EventMusicBuffer` = 0 → task 5 →
  `PlayerEndLevel` sees 5 → `NextArea` → load row = expiry + 1.
- **T_set = grab + 126 + (T + 1) + 32 = grab + T + 159** for a glitch grab (8-2: grab + T + 34);
  with a slide, + slide frames. **Expiry = T_set + (v + 1) + 105**, v = ITC at T_set.
  Every level in the WR matches these formulas exactly.
- Levers that move T_set: the grab frame; the timer value T at the grab (a function of control
  frames, §5 — one fewer unit = one fewer countdown frame, so grab timing relative to the
  24-frame tick matters); fireworks (avoid digits 1/3/6; the WR avoids them everywhere,
  FireworksCounter = $FF); the 126-frame walk and 32-frame raise are geometry/constant.
  The music wait never binds in the WR (`EventMusicBuffer` clears before the timer).

## 7. Pipe transitions
- Down pipe (`VerticalPipeEntry`, GES 3): `ChangeAreaTimer` ($06DE) = **$30 = 48** set when the
  feet meet the pipe-top metatiles ($10/$11); Mario sinks 1 px/frame; load after 48 frames
  (all four WR pipe entries: 565, 3767, 7173, 7724). Warp pipes also set `WorldNumber` at entry.
- Side pipe (`SideExitPipeEntry`, GES 2): `ChangeAreaTimer` from `AreaChangeTimerData` = $A0
  (160) on page 0, else $34 (52).
- Intro areas of 1-2 and 4-2 (`PlayerEntranceCtrl` 6/7): auto-walk right, then `IntroEntr`
  side-pipe countdown (160, page 0), `DisableIntermediate`, `NextArea`. Fixed **499 rows** from
  load to the main-area load; input is overridden (`AutoControlPlayer`).
- No ITC quantization in any of this; the next load's w (§4) is what counts.

## 8. 8-4 and the ending
8-4's four room changes are sub-area loads (Alt 2, +122 each, unquantized). The axe:
`HandleAxeMetatile` (feet on metatile $C5 with non-negative Y speed) sets `OperMode` = 2 /
`OperMode_Task` = 0 and `Player_X_Speed` = $18 the same frame — the movie's last frame. No
timer is involved: every frame saved anywhere in 8-4 counts 1:1, including the 19-frame
input-free coast (H1).

## 9. Summary of constants
| Quantity | Value | Source |
|---|---|---|
| Framerule period | 21 frames (ITC reset value 20) | `DecTimers` |
| Level start (main entry) | control = load + 154 + w, w = ITC at load+8 | §4, 6/6 loads |
| Sub-area entry | control = load + 43 (side) / +122 (vertical exit) / +27 (4-2 wrong warp) | dump |
| Glitch grab → castle door | 126 frames in 1-1/4-1/8-1 (8-2: 1; 8-3 slide+walk 173) | dump |
| Countdown | T + 1 frames | `AwardGameTimerPoints` |
| Flag raise | 32 frames | dump, 5 levels |
| End wait | (v + 1) + 105 frames | `DelayToAreaEnd` |
| Down-pipe | 48 frames | `ChangeAreaTimer` = $30 |
| Side-pipe | 160 (page 0) / 52 | `AreaChangeTimerData` |
| 1-2 / 4-2 intro | 499 rows | dump |
| Game timer | 401 at load; −1 on the first control frame, then every 24 eligible frames | `RunGameTimer` |
| Boot → menu | Start accepted from row 34; rows 34–43 all give control at 197 | §3 |

## 10. Open items for later units
- Exact slide length as a function of grab height (P2.x objective for non-glitch grabs).
- Whether `TimerControl` freezes (injury, size change) or pause (`GamePauseStatus`) can shift the
  ITC phase relative to the level (H3) — they stop `DecTimers` but the NMI keeps running;
  P0.7 catalogs pause/Select effects.
- The load lag frame: which routine overruns, and whether any area/object state changes it.
