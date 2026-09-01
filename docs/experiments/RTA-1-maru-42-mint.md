# RTA-1: how the no-L+R TAS mints the 4-2 wrong warp, and why the human trick is a coin flip

**Unit:** first unit of a new track — **make 4-2 as easy as possible for humans** (not faster: the
level is framerule-quantized and the human "Lightning 4-2" already reaches the TAS's framerule, F36).
Mac session driving the Fedora box over ssh, 2026-08-31/09-01. One movie download, one core replay,
~30 perturbation replays (1.2 s each). No engine search.

**Question.** A top runner drops the 4-2 wrong-warp setup constantly: "jump, slide up the left side
of the block facing backwards; when it works Mario is facing backwards with his legs apart; sometimes
he isn't, and nobody knows why." What is the RAM condition behind that tell, and how wide are the
input windows?

## 1. The movie

Maru's **"warps, RTA rules" TAS** (no Left+Right, 4:57.54; F3) — the human-legal optimum. Found via
the TASVideos submission thread (#6456, zdoroviy_antony/Maru) → speedrun.com thread 1wd01 →
`http://dehacked.2y.net/microstorage.php/get/315676946/Maru_SMB1_RTARulesTASImprovement.fm2`.
Committed as `data/wr/maru-rtarules.fm2` (third-party research input, like HappyLee's; README §Third-party).

- 17,882 records (= 17,868 + the 14 of F3), `romChecksum` identical to ours, **0 records with L+R,
  0 with U+D** (checked over every record).
- Replays on the QuickNES core end to end: `python3 tools/fm2_to_inputs.py data/wr/maru-rtarules.fm2
  data/wr/maru_inputs.bin` then `./build/harness third_party/QuickNES_Core/quicknes_libretro.so
  'roms/Super Mario Bros. (W) [!].nes' data/wr/maru_inputs.bin --input-skip 2 --reset0 --ram
  runs/qn_maru.ram` — **17,880 frames in 1.204 s (14,847 fps)**, `OperMode` 2 (victory) at row 17879.
- Level loads (QuickNES rows; WR's FCEUX rows − 3 for comparison): 1-2 @1942 (WR 1942), 4-1 @3767
  (WR 3764), 4-2 @6040 (WR 6040), main area @6539 (WR 6539), 8-1 @7724 (WR 7721), 8-2 @10811 (WR
  10811), 8-3 @12954, 8-4 @15055 (both = WR). So Maru loses 3 frames into 4-1 and 3 into 8-1 (both
  absorbed by the next framerule) and 14 in 8-4 — exactly F3's 14. **Its 4-2 main area enters the
  wrong-warp pipe on row 7167, the same row as HappyLee's.**

## 2. Maru's 4-2 main area (`tools/rta_mint_trace.py runs/qn_maru.ram 6690 7200 --every 10`)

**Top route.** Floor to col 29, up through the col-29 notch onto the brick run, along the top past
the three goombas, drops off the end of the run at col 48, runs **under** the (50,7)–(51,7) pair on
the floor, jumps up into the left face of the (54,7)–(56,7) group, lands on top of it, jumps the
lift pit (no lift ride), pipes A/B jumped, onto the warp pipe at x 1348, Down.

**Two mints of +10 px each, same recipe, both airborne into a block's left face while facing LEFT:**

| mint | rows | face | contact | offset |
|---|---|---|---|---|
| 1 | 6783–6798 | col 30's face (rising through the notch) | x 466, y 126, rising | 112 → **122** |
| 2 | 6951–6966 | (54,7)'s left face | x 852, y 120, rising | 122 → **132** |

Each: one impede (`SideCollisionTimer` ← 16, `Player_X_Speed` ← 0, `ScreenLeft` frozen), then
15 frames of accelerating right inside the freeze: speeds 0,0,2,3,5,7,8,10,12,13,15,16,18,20,21,23
→ +11 px of x, +10 of offset (1 lost at the impede). 122 + 10 = **132 exactly — zero margin.**
Pipe entry: row 7167, x 1348, `ScreenLeft` 1216, offset 132, `Player_X_Scroll` 0 → `AreaPointer`
stays $2F → 8-1 (both F120 and F129's conditions met).

**The inputs of mint 2** (`--rows 6925 6970`; row r shows fm2 record r+1 — verified: row 6937's
pad `B+Left` is record 6938 `.L....B.`):

```
records 6934-6937  B+Right      full speed (40) on the floor under (50,7)
record  6938       B+Left       ONE frame, last ground frame: facing -> 2 (left), speed stays 40
records 6939-6950  A+B          jump, stick NEUTRAL, 12 frames (speed holds 40 in the air)
records 6951-6957  A+B+Right    Right back ~1 frame before contact; impede on row 6951
records 6958+      B+Right      keep running through the 15-frame freeze
```
Mint 1 is the same with a 2-frame Left tap (records 6771–6772) and Right back at 6779.

Facing never updates in the air (rows 6951–6966: Right held, facing stays 2; flips to 1 on the
landing row 6967), so the ground tap is what leaves Mario facing left through the whole freeze.

## 3. Perturbations (`tools/rta_mint_probe.py`, 19 + 10 variants)

| variant | contact | offset after | warp |
|---|---|---|---|
| **base** | impede @6951, y 120, facing 2 | **132** | **8-1** |
| no Left tap, Right on the last ground frame | same impede, same y, facing **1** | 126 (+4) | fails |
| no Left tap, neutral | same, facing 1 | 127 (+5) | fails |
| Left tap 2 frames before the jump, Right on the last ground frame | facing 1 | 127 | fails |
| Left tap 2 frames long | speed lost, **no impede** | 122 (+0) | fails (and dies later) |
| jump 1 / 2 / 3 frames **early** | feet at y 117/114/112 at the wall → **onto the block, no impede** | 122 (+0) | fails |
| jump 1 / 2 / 3 frames **late** | contact at y 123/126/129, **two impedes** | 131 (+9) | fails by 1 px |
| Right back at record 6945 / 6950 / 6952 | +10 | 132 | entry has `Player_X_Scroll` 1 with the movie's unchanged pipe approach → fails (F129) — the mint itself is fine |
| Right back at 6948 / 6953 / 6955 | +9 / +9 / +8 | 131 / 131 / 130 | fails |
| Right held for the whole jump (no neutral) | +9 | 131 | fails |

**Reading.**
1. **Facing left is the mint amplifier.** Same impede, same contact, same number of impedes — facing
   right yields +4–5 px, facing left +10. With facing opposite to the pressed direction at speed 0
   the game applies the turnaround ("fast accel") acceleration for the whole freeze window; this is
   the human-legal half of what HappyLee's L+R buys (F123's "L+R-doubled acceleration": +21 px in one
   freeze, hence one mint instead of two). On the ground facing flips back on the first Right frame,
   so a **standing** wall-walk without L+R is the +4–5 kind — three or four freezes for 20 px.
2. **The jump window is exactly one frame.** Earlier → no contact (lands on the block); later →
   lower contact, a second impede, one frame of acceleration lost, 9 px.
3. **The Left tap must be exactly one frame long and exactly on the last ground frame.** Two frames
   costs speed and loses the contact; a Right frame after it re-flips facing.
4. **Even done perfectly the total is 132 on the nose.** Mint size is 9–11 px depending on the x
   subpixel at contact (the Right re-press frame changes it: 6945/6950/6951/6952 → 10, 6948 → 9).
   A subpixel-unlucky 9 anywhere fails the warp with every input correct — the runner's
   "sometimes it just doesn't count".
5. The "legs apart" of the tell is the running animation frame while facing left — i.e. the fast-accel
   state itself is what the runner is seeing.

## 3b. Mint 1 (the notch / col-30 face) is just as tight (`tools/rta_mint_probe.py --set mint1`)

Motivation: the runner (from the videos) has **no early mint** — he goes over the 22–26 bricks, not
under — and his second mint is a **wall jump on the warp pipe's own left face** ("falling, hits the
side, jumps back up, goes in"), which the community caps at "9–10 xpos AT MAX" (`community-claims.md`)
and which is F93's foot-check impede entered from a fall. So his line is (50,3) +10 and pipe wall jump
+9–10 = 131–132. Question: is Maru's notch mint an easier +10 that could replace the wall jump?
Offset read at row 6830 (after mint 1, before mint 2); Maru's tap here is 2 frames (records 6771–6772).

| variant | contact | offset after | note |
|---|---|---|---|
| **base** | 1 impede @6783, y 126, facing 2 | **122** (+10) | warp works |
| tap 1 frame instead of 2 | 2 impedes | 121 (+9) | |
| Right on the last ground frame / no tap | 3 impedes, facing 1 | 114 (+2) | facing right again ~nothing |
| tap 3 frames | 1 impede | 122 (+10) | downstream desync of the fixed movie inputs |
| jump 1–3 frames early | 4 impedes, contact y 147–153 | **111 (−1)** | mint lost entirely |
| jump 1–3 frames late | 2–3 impedes, y 129–136 | 120–121 (+8/+9) | |
| Right back at 6779 (movie) / 6780 / 6781 | 1 impede | 122 (+10) | 3-frame window for this input |
| Right back at 6775 / 6777 / 6778 / 6783 / 6785 | 2 impedes | 120–121 | |
| Right held all jump | 2 impedes | 121 | |

**Reading.** Jump window 1 frame again; the tap must be exactly 2 frames here; Right-back has a
~3-frame window. **No variant of either mint exceeds +10.** The 10 is structural for a no-L+R mint:
15 frames of fast-accel from speed 0 = 11 px of x, minus the pixel the impede costs. So the
"one pixel of margin" idea of §4 is **not available from simple perturbations of Maru's inputs** —
a two-mint human line has zero margin by construction, and 122 + 9 = 131 is the failure everyone sees.

## 4. What it means for making it easy

- **The budget is the constraint.** Maru's line is the no-L+R optimum and enters the pipe on the WR's
  row, with the WR's framerule slack of 8 (F29) minus the 3 it loses in the warp-zone room: **single-digit
  frames of slack** at the framerule. Any easier mint must cost **≤ ~5 frames more than Maru's**;
  standing mints (~30+ frames for 20 px at +4–5 per freeze) are out.
- ~~The cheap lever is one pixel of margin.~~ **Refuted in §3b**: no perturbation of either mint
  exceeds +10; 10 per freeze is the no-L+R ceiling, so any two-mint line is 132 with zero margin.
  Margin therefore needs **more contacts**, not a better-timed one. A first draft of this section
  proposed a "tall-face slide" (the warp pipe's or pipe B's face) as a > 10 px shape — **withdrawn
  (user's catch):** the warp pipe's face is exactly where the runner's wall jump mints, and it gives
  9–10 — the same 15-frame fast-accel arithmetic — so the one existing measurement of a tall-face
  contact is evidence *against* a > 10 shape; and pipe B's top (row 4, y 64) is not reachable in one
  jump, so a slide up it has no "run over the top" phase at all. **No known no-L+R mint is worth more
  than 10.**
- **The only route to margin is a third contact** — notch +10, (50,3) +10, pipe wall jump +9–10 ≈ 30,
  i.e. 8–10 px of slack that widens *all three* windows from 1 frame to several. Cost: one more speed
  reset, ~15–18 frames (F123), against ~5 frames of framerule slack ⇒ **one framerule (21 frames)**,
  which is presumably the pre-Lightning human route. **Whether "easy" is worth a framerule is the
  user's call**, and it decides the deliverable:
  - *No* → consistency setups (visual cues, position-based) for two 1-frame tricks, plus one cheap
    engine question: is there *any* three-contact line inside Maru's + 5? (`bfscx --goal-offset 137`,
    human inputs, S2 arrival root; expected dry, and dry is an answer.) Check F129's `goal_refused` first.
  - *Yes* → build the 3-mint line from Maru's inputs plus a wall jump on the core, and measure each
    window with `tools/rta_mint_probe.py` under 8 px of margin.
- **The runner's line differs from Maru's in where mint 2 is.** From the user's description of the
  videos (Niftski): he stays on the brick-run top, "slides up the left side of the block facing
  backwards", goes **over** the upper (50,3)–(51,3) pair and comes down to the three group. So his
  mint 2 is on **(50,3)'s left face, rising, under the roof** (2 tiles of headroom) — same recipe as
  Maru's, different face; Maru instead drops to the floor, runs under the lower pair and mints on
  (54,7). Where his mint 1 is depends on how he gets onto the brick run: through the col-29 notch
  (then it is Maru's col-30 mint) or from the run's left end at col 22 (unknown — check the video).
  The (50,3) face needs its own replay from the top-route chain (`runs/P2.3c-2c/chain_s2p.bin`, whose
  F113 arc passes over it at Y ≈ 38 without contact — a shorter arc is the runner's).

## 5. Reproduce

```
python3 tools/fm2_to_inputs.py data/wr/maru-rtarules.fm2 data/wr/maru_inputs.bin
./build/harness third_party/QuickNES_Core/quicknes_libretro.so 'roms/Super Mario Bros. (W) [!].nes' \
    data/wr/maru_inputs.bin --input-skip 2 --reset0 --ram runs/qn_maru.ram
python3 tools/ram_trace.py runs/qn_maru.ram 1 17880 WorldNumber LevelNumber AreaNumber OperMode --changes
python3 tools/rta_mint_trace.py runs/qn_maru.ram 6690 7200 --every 10
python3 tools/rta_mint_trace.py runs/qn_maru.ram 6925 6970 --rows
python3 tools/rta_mint_probe.py            # ~35 s
```
