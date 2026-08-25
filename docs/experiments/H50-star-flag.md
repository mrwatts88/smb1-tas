# H50 — a second StarFlagObject: CONFIRMED on the core, **1,329 frames**

**Unit:** H50 (Track B). Mac session, 2026-08-25, same day as E10 raised it.
**Tool:** `tools/starflag_poke.py` (new). **Harness:** `build/harness --poke` (F251's flag; its
poke cap was raised 8 → 64 this session so N > 2 fits).
**Status:** the *mechanism* is confirmed by direct core measurement — and independently by the
Linux session within the hour (F258, `tools/starflag_probe.py`), which reproduced the N = 2 gains
exactly. F259/F260 below are the extension this file adds: the N-saturation, the music floor and
how to remove it, the health check, and the second reachability question. **Reachability is not** —
it needs the same missing write primitive as H43, which E10 narrowed the same day (F252).

## Reproduce

```
tools/build_core.sh                     # or just: clang -O2 -o build/harness src/fastcore/harness.c \
                                        #   -I third_party/QuickNES_Core/libretro/libretro-common/include
tools/starflag_poke.py --n 2                       # all five flag levels
tools/starflag_poke.py --n 2 --no-music            # + suppress the win music
tools/starflag_poke.py --level 1-1 --n 2 -v        # per-level detail
```

Every run does a control pass with the unmodified WR inputs first and reports both, so the
control is built into the measurement rather than remembered.

## The claim (F254, from E10)

`RunStarFlagObj` is dispatched **once per frame per enemy slot** whose `Enemy_ID` is
`StarFlagObject` ($31) — `GameEngine` `ProcELoop` x = 0…5 → `JmpEO` entry 29. Everything it
drives is global (`StarFlagTaskControl`, `GameTimerDisplay`) **except the one byte task 4 blocks
on, which is per slot**:

- task 2 `AwardGameTimerPoints` subtracts one timer unit per *call* → N calls per frame;
- task 3 `DrawFlagSetTimer` writes `EnemyIntervalTimer[i] = 6` for **its own** slot and bumps
  the task to 4;
- task 4 `DelayToAreaEnd` reads `EnemyIntervalTimer[x]` for **its own** slot — so a second
  object, processed later in the same frame, reads its own untouched **0**, falls through
  `EventMusicBuffer`, and advances to task 5.

That (v+1)+105 wait *is* the framerule (F27).

## Result 1 — two star flags, music untouched

`tools/starflag_poke.py --n 2` (core frames; the control column is the real WR):

| level | countdown | raise | area-end wait | next area load | saved |
|---|---|---|---|---|---:|
| 1-1 | 371 → 185 | 32 → 32 | 126 → 48 | 1941 → 1677 | **264** |
| 4-1 | 341 → 170 | 32 → 32 | 118 → 64 | 6039 → 5814 | **225** |
| 8-1 | 201 → 100 | 32 → 32 | 109 → 132 | 10810 → 10732 | **78** |
| 8-2 | 339 → 169 | 32 → 32 | 108 → 131 | 12953 → 12806 | **147** |
| 8-3 | 245 → 122 | 32 → 32 | 117 → 97 | 15054 → 14911 | **143** |
| | | | | | **857** |

Both halves fire exactly as predicted: the countdown halves to the frame, and
`DelayToAreaEnd` stops honouring the interval timer (1-1: it advances at core 1676 with
`EnemyIntervalTimer[0]` still reading **4**).

**But a new floor appears.** With the countdown halved, the binding condition becomes
`DelayToAreaEnd`'s *second* test, `EventMusicBuffer == 0` — the end-of-level music, whose length
is fixed and anchored to the castle walk. That is why 8-1 only gains 78 (its wait *grew* 109 →
132: T = 200 is already short, so it was waiting on the music before and now waits longer).

**N > 2 buys nothing.** At N = 3, 4 and 5 the countdown keeps shrinking (1-1: 123, 92, 74) and
the area-end wait absorbs it exactly — 1-1's next load is core 1677 at every N. The music is a
hard floor.

## Result 2 — drop the music too

`PlayerEndLevel` (smbdis 5831) queues the win music only if `ScrollLock` is still set when
Mario passes `Player_Y_Position` ≥ $AE:

```
ChkStop: lda Player_Y_Position / cmp #$ae / bcc …
         lda ScrollLock / beq ChkStop      ; <-- clear ScrollLock here and the music never queues
         lda #EndOfLevelMusic / sta EventMusicQueue
         lda #$00 / sta ScrollLock
```

`--no-music` clears `$0723` on the frame before that check. `EventMusicBuffer` then stays 0 for
the whole sequence, and with two star flags **`StarFlagTaskControl` goes 3 → 5 in a single
frame** — task 4 is skipped entirely:

| level | countdown | raise | area-end wait | next area load | saved |
|---|---|---|---|---|---:|
| 1-1 | 371 → 185 | 32 → 32 | 126 → **0** | 1941 → 1629 | **312** |
| 4-1 | 341 → 170 | 32 → 32 | 118 → **0** | 6039 → 5750 | **289** |
| 8-1 | 201 → 100 | 32 → 32 | 109 → **0** | 10810 → 10600 | **210** |
| 8-2 | 339 → 169 | 32 → 32 | 108 → **0** | 12953 → 12675 | **278** |
| 8-3 | 245 → 122 | 32 → 32 | 117 → **0** | 15054 → 14814 | **240** |
| | | | | | **1,329** |

1-1 in detail (`-v`): control `SFTC 2@1411 3@1782 4@1814 5@1940`, poked
`SFTC 2@1411 3@1596 5@1628`.

## The run stays healthy

Checked past the early exit on 1-1 (`--frames 2400`, same pokes): 1-2's intro area loads at core
1629 and runs normally (`ScreenRoutineTask` 0…12, `OperMode_Task` 3 at 1790), the intro pipe
hands off to 1-2's main area at 2125 with `ScreenRoutineTask` jumping 6 → 8 (the
`DisableIntermediate` sub-area path, exactly as in the control), player control at 2150, **game
timer reloads to 400**, lives unchanged at 2, `GameEngineSubroutine` cycles 0/7/8 normally. No
death, no reset, no desync of the game's own state machine. (Everything after the poke is of
course off the WR's input timing — that is expected and is why each level is measured in
isolation.)

## What this is worth, honestly

- **The framerule is gone in the levels where this fires.** With the wait at 0 the exit is
  `grab + 126 + ⌈T/2⌉ + 1 + 32`, all frame-granular — so a frame saved in the level is worth a
  frame, not "worth 0 unless it crosses a boundary". `docs/open-threads.md`'s budget table
  ("a level only pays if it saves its whole framerule deficit") stops applying, which is worth
  more than the 1,329 itself: it revives the 78 frames of per-level deficit *and* every
  sub-threshold banked frame.
- **1,329 is a per-level sum, not yet a route number.** Each level was measured in isolation
  against its own control. Chained, the savings are additive (nothing re-quantizes them), but
  the *entry* of the next level still costs 154 + w with w = ITC at load+8 (F28) — and with
  unquantized exits w becomes a free variable per boundary. So the route figure is
  1,329 ± ~20 per boundary, and could be pushed slightly **up** by choosing exits that land on
  w = 0. That needs a route-level assembly, not this measurement.
- **It is not reachable yet.** Both halves need a write:
  - the second flag: `Enemy_ID+k = $31` and `Enemy_Flag+k = 1`, i.e. a non-zero byte into an
    enemy slot — the frenzy cells `$06CB`/`$06CD` do exactly this (F206), and F252 has just
    shown the block-buffer path cannot reach them with a non-zero value;
  - the music: `ScrollLock` ($0723) = 0 at one frame. Checked: **none of the five flag levels
    contains a `ScrollLockObject`** (`tools/area_data.py` over L_GroundArea6/3/17/19/2), so
    there is no in-game toggle either. $0723 is also far above F203's $06CF ceiling.

## What it changes for the plan

The ACE line (H7/H8/H43) had a confirmed arbitrary-jump primitive and **no known payoff** —
F208's summary is "no value found yet ends the game early". It now has one, and it does not need
a jump at all: **one known byte into one known cell is worth 1,329 frames and deletes the
framerule.** That is a much smaller target than "steer a computed jump somewhere useful", and it
re-prices every remaining write-primitive question — P3.1 §4's unaudited classes (stack
over/underflow, non-indexed writes, `VRAM_Buffer` overflow), which after F252 are all that H43
still rests on.
