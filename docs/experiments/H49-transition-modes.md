# H49 — 8-4's pipe-exit animation, and why `WarpZoneControl` does not collect it

**Raised and refuted 2026-08-25 (session 19), from the user's question about the transition screens.**
Facts: F249 (the measurement), F250 (the `$06CB` re-pricing), F251 (the refutation).
Hypothesis: H49 (refuted; residual folded into E10).

---

## 1. Setup

No search. The disassembly, `data/wr/fceux_wr.ram`, and one new harness flag.

**New tooling this unit:** `build/harness --poke ADDR=VAL@FRAME` (`src/fastcore/harness.c`), which
writes one RAM byte immediately after the given frame's `retro_run()`. Up to 8 pokes. Built with
`tools/build_explore.sh`'s compiler line or:

```sh
gcc -O2 -march=native -std=gnu11 -I third_party/QuickNES_Core/libretro/libretro-common/include \
    -o build/harness src/fastcore/harness.c -ldl
```

**Frame convention:** `--input-skip 2`; core frame `f` consumes input byte `f+2`; in 8-4 the FCEUX
dump row is core + 4 (verified: dump 12288 = core 12284, x 3258 / y 96).

---

## 2. The measurement (F249)

Each of 8-4's four sub-area loads sits in `GameEngineSubroutine` 7 (`PlayerEntrance`) for **exactly
96 frames**, moving Mario 1 px/frame from `Player_Y_Position` `$f0` (240) to `$90` (145) — that is
`EntrMode2`, the rise-out-of-a-pipe animation. Player control starts at **load+122**; every mode-0/1
sub-area entrance on the route starts at **load+43**. **79 frames per transition, 316 across the
four, in the only unquantized level.**

```sh
tools/slack_table.py data/wr/fceux_wr.ram        # the delay column
```

The mode is chosen in `VerticalPipeEntry` (smbdis 5684-5695) by two branches — `WarpZoneControl != 0`
→ mode 0, else `AreaType != 3` → mode 1, else mode 2 — and committed in `ChgAreaPipe` only on the
frame `ChangeAreaTimer` expires, **~48 frames after `HandlePipeEntry` already fixed the
destination**. So a mid-descent `WarpZoneControl` should buy the fast entrance without warping.

---

## 3. The test, and the exact commands

Control and poke, at 8-4's first sub-area transition (descent = core 15744-15792, `ChangeAreaTimer`
48 → 0; poke at 15770, 22 frames in):

```sh
CORE=third_party/QuickNES_Core/quicknes_libretro.so
ROM="roms/Super Mario Bros. (W) [!].nes"
./build/harness $CORE "$ROM" data/wr/wr_inputs.bin --frames 16400 --input-skip 2 --ram /tmp/c84.ram
./build/harness $CORE "$ROM" data/wr/wr_inputs.bin --frames 16000 --input-skip 2 \
    --poke 0x6d6=1@15770 --ram /tmp/p84.ram
```

Then read `GameEngineSubroutine` ($000e), `AltEntranceControl` ($0752), `ScreenTimer` ($07a0),
`ScreenRoutineTask` ($073c) and `AreaPointer` ($0750) per frame.

## 4. Result

| | control | poked `$06D6 = 1` @15770 |
|---|---|---|
| `AltEntranceControl` at the entrance | **2** | **0** |
| `PlayerEntrance` (GES 7) | **96 frames** (15818-15913) | **1 frame** (15955) |
| `Player_Y_Position` during it | 240 → 145 | 80 (no rise) |
| `AreaPointer` at control | `$e5` | **`$e5` — unchanged** |
| `ScreenTimer` ($07a0) nonzero | **0 frames** | **170 frames**, first value **7** at 15800 |
| `ScreenRoutineTask` 7 (card) | never | **yes** |
| player control at | core **15914** | core **15956** |

**The mechanism works exactly as derived** — the entrance collapses 96 → 1 and the pipe destination
is untouched, confirming that `HandlePipeEntry` having already run makes a mid-descent
`WarpZoneControl` safe. **And it is 42 frames worse**, because `AltEntranceControl` = 0 is the *only*
mode that can reach `DisplayIntermediate`'s card path:

```
DisplayIntermediate:                       ; smbdis 1540-1556
  lda AltEntranceControl
  bne NoInter          ; modes 1/2/3 -> no card
  ldy AreaType
  cpy #$03
  beq PlayerInter      ; CASTLE -> card shown unconditionally, DisableIntermediate BYPASSED
  lda DisableIntermediate
  bne NoInter
```

8-4's rooms are `AreaType` 3, so mode 0 always shows the card: **137 frames against 96 saved.** The
`ScreenTimer = 7` write at 15800 is F28's card signature and is observed directly, not inferred.

Second finding from the same trace: mode 0 spawns Mario from **`HalfwayPage`, not `EntrancePage`**
(smbdis 2669) — for room 2 that is page 0 instead of page 7, a large regression on its own.

## 5. Conclusion

**H49 refuted.** The mode that would pay is **mode 1** (no rise *and* no card), which
`VerticalPipeEntry` gives when the room being *left* is not a castle. 8-4's rooms are castles and
`AreaType` ($074e) is far above F203's `$06CF` OOB ceiling.

**Residual, and it is exact.** The one 8-4 transition whose *destination* is not a castle is the
water room (load 16598, `AreaType` 0). There `DisplayIntermediate` does consult `DisableIntermediate`
($0769), so **`$06D6` non-zero AND `$0769` non-zero during that one descent is worth ~96 frames**
with a 16 px setback. Two writes, neither in the proven window → **E10**, not a testable hypothesis.

**What survives independently (F250).** `WarpZoneObject` is enemy routine `$34` and its whole body is
`inc WarpZoneControl` given `ScrollLock != 0` and Mario's Y even; `CheckFrenzyBuffer` copies `$06CB`
into `Enemy_ID` unchecked; and **`$06CB` is inside F203's `$06CF` ceiling, unlike `$06D6`**. The OOB
programme has been aiming at a byte it cannot reach while a byte it *can* reach drives real
machinery. That re-pricing stands regardless of this unit's negative.

## 6. Method note

Twice in one session the derivation and the measurement disagreed: the 8-2 jump arc said "misses by
1-2 px" and the core said "clears by 2" (F247); this unit's code read said "+79 frames" and the poke
said "−42". **Derive to find the question, measure to answer it.** `--poke` exists so the next one of
these costs ten minutes.
