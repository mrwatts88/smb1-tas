# The swim section: a 259-frame door that is locked by one speed unit

**Unit:** H12 leftover (i) — the route's only swim section, which `docs/input-semantics.md` §4 had
skipped on the explicitly false premise "no water on the WR route". Linux box, 2026-08-25 session 21.
Reading plus three harness runs.

**Why it mattered.** 8-4's water room is **696 route frames**, 1,020 px, and **667 of those frames run
at the swim cap of 24 subpixels/frame (1.5 px)** against the 40 (2.5 px) the same Mario manages on
land (F67/F265 `r4`). It is the longest single stretch of the route spent below the running cap, it
sits in the only unquantized level, and nobody had read its input semantics.

## 1. Water runs four different caps, and one of them is the running cap

`X_Physics` (smbdis.asm 6139) picks the cap index `Y` and then loads `MaxRightXSpdData,y`
(`.db $28, $18, $10, $0c` = 40 / 24 / 16 / 12):

| situation | path | Y | cap |
|---|---|---|---|
| swimming (`Player_State != 0`), `Player_XSpeedAbsolute` **< $19** | `bcc ChkRFast` → `iny` | 1 | **24** |
| swimming, `Player_XSpeedAbsolute` **>= $19** | `bcs GetXPhy` | 0 | **40** |
| standing on the water floor (`Player_State == 0`) | `ProcPRun` → water → `ChkRFast` → `iny` | 2 | **16** |
| pipe entrance (`GameEngineSubroutine == 7`) | `ldy #$03` | 3 | 12 |

So the game will happily let Mario swim at the **full running cap** — the test is on
`Player_XSpeedAbsolute`, and the threshold is **$19 = 25**.

**The swim cap is 24. The unlock threshold is 25. One unit.**

## 2. The door is real — measured

`build/harness … --poke 0x700=0x19@F` for 60 consecutive frames in the water room (forcing
`Player_XSpeedAbsolute` = 25), with Right held:

```
frame  spd  absSpd  maxRight    x  | unpoked spd    x
16800   24     25       24    158  |      24      158
16802   26     25       40    161  |      24      161
16820   14     25       40    169  |      24      188
16845   36     25       40    209  |      24      225
16859   40     25       40    244  |      24      246
```

`MaximumRightSpeed` becomes 40 on the next frame and the actual speed climbs to **40 and stays
there** — Mario swims at 2.5 px/frame. (The dip at 16805 is a terrain bump: forcing Right desyncs him
from the WR's line. Irrelevant to the mechanism.)

**Worth:** 1,020 px at 1.5 px/frame = 667 frames; at 2.5 px/frame ≈ 408. **≈ 259 frames**, in the
level where a frame is worth exactly one frame.

## 3. The handle cannot be reached — complete enumeration

`Player_XSpeedAbsolute` is written in exactly one place, `SetAbsSpd` at the end of `ImposeFriction`
(6265), and it stores `|Player_X_Speed|`. So the question reduces to: **can `Player_X_Speed` reach 25
inside a water area?** Every writer of `Player_X_Speed` in the ROM:

| site | what it writes |
|---|---|
| 5449 `KeepOnscr` | 0 |
| 5719 / 5724 `EnterSidePipe` | **8**, or 0 when the low nybble of X is 0 |
| 6219 `ProcSkid` | 0 |
| 6243 / 6247 `ImposeFriction` (rightward) | accelerates, then **clamps to `MaximumRightSpeed`** |
| 6255 / 6259 `ImposeFriction` (leftward) | accelerates, then clamps to `MaximumLeftSpeed` |
| 12133 `HandleAxeMetatile` | the axe, 8-4's Bowser room — not a water area |
| 12210 `PutPlayerOnVine` | 0 |

The only writer that can *raise* the speed is `ImposeFriction`, and it clamps at the cap, which in
water is 24. And the value cannot arrive stale from the previous room: `InitializeArea` calls
`InitializeMemory` with `ldy #$4b`, clearing **$0700–$074B**, and `Player_XSpeedAbsolute` is **$0700**.

**Confirmed in play:** holding Right for 60 straight frames in the water room pins the speed at
exactly 24 with `absSpd` = 24 (the "unpoked" column above), and the moment Mario touches the floor it
drops to 16.

## 4. Verdict

**Closed.** The swim section cannot be sped up by any input. It is not a search question, a routing
question or a glitch question — it is a one-unit arithmetic lock, proven by enumerating the eight
writers of a single byte. The 259 frames are real and unreachable.

Worth keeping in view for exactly one reason: **if some other mechanism ever adds even 1 to
`Player_X_Speed` inside a water area, it unlocks 259 frames**, because the cap flips to 40 and stays
there (the poked run shows the state is self-sustaining once above the threshold). That is a far
larger prize than anything on the live board, from a single unit of speed.

## 5. Reproduce

```
./build/harness third_party/QuickNES_Core/quicknes_libretro.so "roms/Super Mario Bros. (W) [!].nes" \
    data/wr/wr_inputs.bin --frames 16900 --ram /tmp/w.ram --reset0 --input-skip 2 \
    --poke 0x700=0x19@16800 … (one per frame; the harness caps at 64)
```
then read `$57` (speed), `$0700` (absolute), `$0456` (MaximumRightSpeed) per frame.
