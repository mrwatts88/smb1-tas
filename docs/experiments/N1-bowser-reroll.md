# N1 — Enter the Bowser room one frame late: Bowser's walk range re-rolls and the last input moves 3 frames earlier

2026-11-09, Mac session (box left alone: H52's two-jump job was running on all 12 threads).
Facts F305–F311, hypothesis H53. Tool: `src/fastcore/endlab.c` (`tools/build_endlab.sh`).
One-command reproduction: `tools/n1_build_candidate.sh` (about 3 minutes).

## Result

`data/candidates/smb1-warps-n1-17846.fm2` — 17,846 input frames, ending on its last input.

| | last input (fm2 line, 0-based) | axe touched (fm2 frame, 0-based) | input-free tail |
|---|---|---|---|
| WR #1715M | 17848 | 17867 | 19 |
| N1 | **17845** | 17868 | 22 |

- **Last input is 3 frames earlier than the WR's.** This is the project's bar (F17) and the
  TASVideos timing rule ("TAS timing begins at power-on and ends on the final necessary input",
  F311).
- **The axe is touched 1 frame later than in the WR.** That is the price of the lever (below). A
  judge comparing by axe frame would call this 1 frame slower. Both numbers are stated wherever the
  result is cited.
- Verified on three emulators (F310): QuickNES core (Mac), FCEUX 2.6.6 and BizHawk 2.11.1/NesHawk
  (box). FCEUX and NesHawk agree on all 22 dumped addresses over 18,268 common frames; both show
  the movie leaving playback at 17,846 frames and `OperMode` = 2 at fm2 frame 17868; 24 lag frames,
  the same rows as the WR up to the edit.

## Why there was room (F305)

The WR is at the speed cap from core 17618 on, and air keeps x-speed, so Mario's x(t) is fixed.
His right foot enters the axe column (page 18, x 208) on dump row 17868 for every full-speed line.
The axe needs a foot in row 6 (Mario Y in [96, 112)) with non-negative y-speed. So the last input of
a jump with A held k frames is `17868 - C(k)` in dump rows, where `C(k)` is the number of frames
between the last held frame and the last frame of the Y window. `tools/jump_coast_table.py`
reproduces the WR's two jumps exactly (hold 6 and hold 32) and gives, from the bridge at cap speed:

| hold k | 1 | 6 (WR) | 8–10 | 11–13 | 14–21 | **22** | 23–30 | 31–32 |
|---|---|---|---|---|---|---|---|---|
| C(k) | 15 | **18** | 19 | 20 | 21 | **22** | 21 | 20 |

With nothing in the way the last input would be 4 frames earlier than the WR's. The whole gap is
Bowser.

## Bowser in this room (F306)

From `InitBowser` / `BowserControl` and the WR dump (rows 17756–17869):

- **Hop:** `EnemyFrameTimer` is set to $20 at spawn, so the first hop starts 31 frames after the
  spawn, every time. It lasts about 70 frames (Y 128 → 92 → 129). The WR crosses during it.
- **Walk:** on every frame with `FrameCounter & 3 == 0` he moves by `BowserMovementSpeed`, which
  starts at +2 (away from Mario). He turns back when he is `MaxRangeFromOrigin` from his origin.
- **The range is one random draw:** on the first such frame after the spawn,
  `MaxRangeFromOrigin = PRandomRange[PseudoRandomBitReg[slot] & 3]` with
  `PRandomRange = $21, $41, $11, $31`. In the WR Bowser is in slot 1 and the draw is at dump row
  17762: byte 1 = 198, low bits 2, range **$11 — the smallest of the four**. He turns at x 130
  (page 18) on row 17794 and drifts back at 1 px per 4 frames, so he is at x 124–116, in the air,
  exactly where a long jump has to take off.
- **Hammers** (world 8): tried on every 4th frame of the hop, misc slot from byte 1 of the LFSR,
  held 14 frames above his head, then thrown left. Hammer checks run on odd `FrameCounter`, enemy
  body checks on even.

Hand check of the WR scene with this model: a jump high over him clears his front box by 1 px and
is hit by the hammer thrown on row 17836; anything lower meets his body. That matches F302.

## What cannot be moved for free (F307, F308)

- **Exhaustive control.** `endlab --bfs 17760 17862 --coast 17815 17852` searches every jump timing
  at cap speed (pads B+R and A+B+R, deduplicated on gameplay RAM) from after Bowser's spawn:
  **best last input 17846, the WR's**, in 58 s. The line it finds runs *under* the hopping Bowser
  and jumps out behind his tail on the WR's frame, so that route ties too.
- **Spawn frame.** Bowser loads when `ScreenLeft` reaches page 17, x 65, and in steady state
  `ScreenLeft` = Mario's pixel x − 112. Delaying the spawn one frame needs Mario's x at row 17758
  below 177.0, a loss of more than 272/256 px. Keeping the axe on row 17868 allows a loss of at most
  272/256 px. The two miss by 1/256 px, so every spawn delay costs a frame of arrival. A delay of
  1–3 frames leaves the draw on the same frame (range still $11); 4 or more changes it but costs 4
  or more frames, which the 4-frame ceiling cannot repay.
- **Slot.** The room's slot chain is fixed by the scroll: piranha plants in 0 and 1 from the load,
  Hammer Bro in 4, the podoboo takes slot 2 at row 17657, the frenzy flame takes slot 0 at row
  17745, Bowser gets slot 1. The podoboo comes into range 8 px before slot 0's plant is erased
  (`ScreenLeft` 65 vs 73) and enemy loading is blocked on only one frame per 32 px, so it cannot be
  made to wait for slot 0.

- **Arrival.** The room's acceleration from the pipe exit is the same state sequence as room 2's
  (dump rows 17592–17622 against 15920–15950: x 56 → 94 + 16/256, cap on the 31st frame, the same
  sub-pixels throughout), and room 2's is MrWint's solved speed-up (F66). After the axe the victory
  sequence runs exactly as in the WR, one frame later (bridge collapse 138 frames, messages at
  +324; FCEUX rows 17869/18007/18193 against 17868/18006/18192).

Consequence for the running H52 follow-up: its 12 variants use a Left+Right or no-B frame on the
ground, which clamps speed to 24 and loses about 9 px (4 frames of arrival). With the 22-frame
ceiling that is a tie at best.

## The lever (F309)

`FrameCounter` is cleared by the area load, but the LFSR is not. So if the Bowser room is loaded one
frame later, everything in the room that is timed by `FrameCounter` or by the scroll keeps its place
relative to Mario, and every random draw moves one step along the LFSR. The cost is one frame.

One frame late, the range draw reads byte 1 = 99, low bits 3: **range $31**. Bowser keeps walking
right (x 144 at take-off, 162 at his turn) and the hold-22 jump goes over him.

How the frame is lost: one blank input before core 17412. In the WR Mario lands at the water room's
exit pipe on that frame and enters it; with the blank he is stopped against the pipe and enters on
17413. The room then loads one frame late with the same entry state.

The WR's inputs for the first half of the room do not survive the new draws (shifted one frame,
they die at core 17686, x 4357, next to the Hammer Bro with one of his hammers live), so the first
half is searched again (stage 1) before the ending (stage 2):

```
build/endlab CORE ROM data/wr/wr_inputs.bin --input-skip 2 --insert 17412=0x00 \
    --bfs 17625 17760 --ground-at 17750 --pick 0 --out runs/N1-ending/k1_stage1.bin
    -> checkpoint core 17750: kept 160 grounded nodes of 11777
       picked grounded node 0; jumps: [17636 hold 2] [17683 hold 1] [17715 hold 15]
build/endlab CORE ROM runs/N1-ending/k1_stage1.bin --input-skip 2 \
    --bfs 17750 17868 --coast 17812 17856 --out runs/N1-ending/k1_best.bin
    -> scene: bowser spawn core 17755 slot 1, range $31 set by core 17759 (FC 36)
       SUCCESS last_input=17843 victory=17865  jumps: [17783 hold 1] [17822 hold 22]
       BEST last input = core 17843   (WR 17846)
build/endlab CORE ROM runs/N1-ending/k1_best.bin --input-skip 2 --replay
    -> replay: victory_core=17865  last_nonzero_input_core=17843
```

The ending is unique: of 1,040 live nodes at core 17844 exactly one coasts to the axe, the hold-22
jump the table predicts. 17843 is also the floor for this lever: one frame paid, four gained.

Frame conventions: core frame = fm2 input line − 2 (`--input-skip 2`); FCEUX dump row = core + 4.

## What the search covers and what it does not

- Stage 2 is exhaustive over jump timings at cap speed from core 17750 in that scene. It does not
  include inputs that give up position.
- Stage 1 keeps only full-speed nodes and drops Hammer Bro stomp branches (each stomp frame forks
  the world and multiplies the frontier). It took the first of 160 grounded nodes; the other 159
  were not compared. They differ in leftover state from the first half, which could matter to
  Bowser's hammer slots, but 17843 is already the floor.
- Delays of 2 and 3 frames were not built (two blanks at the pipe leave Mario stuck outside it).
  Their floors are 17844 and 17845; the draws would be $41 and $21.
- A node is restored as one full savestate per frame plus its own 2 KB of RAM (F50). The result
  does not rest on that: the movie was replayed from power-on on three emulators.

## Open

1. **The convention.** By last input N1 is 3 frames faster; by axe touch 1 frame slower. TASVideos'
   rule text times to the final necessary input and says nothing about this trade (F311). Whether
   to treat N1 as the record is the user's call, and submitting is theirs alone (D4).
2. **An axe-neutral version does not exist in this room** at cap speed: the control is exhaustive
   and arrival is pinned. A record by axe frame has to come from upstream.
3. The 12 H52 follow-up jobs on the box can be stopped; see above.
