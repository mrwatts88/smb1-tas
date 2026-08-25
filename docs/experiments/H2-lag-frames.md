# H2 / L5 — the load lag frame: what causes it, and is it ours?

**Unit:** L5 (`docs/open-threads.md`). Mac, 2026-08-25 session 20. **No compute** beyond one
harness dump; the answer is a cycle count.
**Question:** 17 lag frames on the route, exactly one per area load — **five of them inside 8-4**,
where nothing re-absorbs a frame and one frame is the record. The standing prior was "the lag *is*
the load, so probably irreducible", which nobody had ever checked.

## 1. Where they are (WR dump, `lag` column)

24 lag frames total: **7 at boot** (i = 2–6, 8, 9) and **17 at exactly `load + 2`**, one per area
load, with no exceptions:

| load | 43 | 613 | 927 | 1945 | 2444 | 3815 | 6043 | 6542 | 7221 | 7772 | 10814 | 12957 | **15058** | **15796** | **16233** | **16598** | **17468** |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| lag at | 45 | 615 | 929 | 1947 | 2446 | 3817 | 6045 | 6544 | 7223 | 7774 | 10816 | 12959 | **15060** | **15798** | **16235** | **16600** | **17470** |

The last five are 8-4's (one main entry + four sub-area loads), so **8-4 pays 5 lag frames 1:1**.
Every lag frame has `OperMode_Task` = 1 and `IntervalTimerControl` unchanged from the previous row
— no NMI ran, so no timer, no RNG step, no logic. The ITC values at those rows span 0…19, i.e. the
lag is **not** phase-dependent.

(F224 records "16"; the dump has 17. The extra one is 1-1's own load at i = 43, which is easy to
count as part of boot. Immaterial to the conclusion, but the ledger should say 17.)

## 2. Which frame overruns — `ScreenRoutineTask` from the core

The WR CSV has no `ScreenRoutineTask`, so this came from a harness RAM dump (core frame = dump
row − 4). Around 8-4's main load:

```
core   dump   OperMode_Task  ScreenRoutineTask  FrameCounter  DisableScreenFlag
15053  15057        3               12              50              0
15054  15058        0               12 (stale)      51              1     <- ChgAreaMode set task 0
15055  15059        0                0              52              1     <- InitializeArea ran: SRT cleared
15056  15060        1                0               0              1     <- FrameCounter cleared; FCEUX's lag row
15057  15061        1                1               1              1     <- InitScreen ran (VRAM_Buffer_AddrCtrl = 3)
15058  15062        1                2               2              1
```

So the routine that runs on the frame preceding the lost NMI is **`InitializeArea`** (`GameMode`
task 0) — not `InitScreen`, which is the frame *after*. `docs/timing-model.md` §1 attributes the
lag to "the `InitScreen`/`InitializeNameTables` frame"; the cycle count below says otherwise.

## 3. The cycle account

An NTSC frame is **29,780.5 CPU cycles**. The NMI disables NMIs on entry
(`and #%01111110 / sta PPU_CTRL_REG1`) and re-enables them just before `rti`, so a handler still
running at the next vblank **loses that NMI entirely** — no `ReadJoypads`, which is exactly what
FCEUX counts as a lag frame.

**`InitScreen` does not overrun.** `MoveAllSpritesOffscreen` is 64 iterations × 16 = 1,024 cycles.
`InitializeNameTables` writes a full name table twice: the `InitNTLoop` structure
(`ldy #$c0` once, then `dex / bne InitNTLoop` re-entering with y = 0) runs 192 + 3×256 = **960**
tiles, not the 768 its comment claims, plus 64 attribute bytes — 1,024 × 9 = 9,216 cycles per name
table, **18,432** for both. With the prologue that is ≈ 21,500 of 29,780. It fits.

**`InitializeArea` does overrun, and it is `InitializeMemory` that does it** (smbdis 2770):

```
InitByteLoop: cpx #$01        2
              bne InitByte    3   (taken for every page but the stack)
InitByte:     sta ($06),y     6
SkipByte:     dey             2
              cpy #$ff        2
              bne InitByteLoop 3
                              -- 18 cycles per byte
```

`InitializeArea` calls it with `ldy #$4b`, but **Y only shortens page 7** — the loop then clears
pages 6 down to 0 in full regardless. Bytes touched = 76 (page 7) + 7 × 256 = **1,868**:

| region | bytes | cycles |
|---|---:|---:|
| page 7 from $074B down | 76 | 1,368 |
| pages 6, 5, 4, 3, 2, 0 | 1,536 | 27,648 |
| page 1 (≈160 stores skipped by the `cpy #$60` stack guard, ~17 c/byte) | 256 | ~4,350 |
| **`InitializeMemory` total** | **1,868** | **≈ 33,370** |

Plus the rest of `InitializeArea` (`GetAreaDataAddrs`, the `ClrTimersLoop`, the header decode) and
the NMI prologue (OAM DMA 513, `SoundEngine`, `ReadJoypads`, `DecTimers`, the LFSR step ≈ 2,000):

> **≈ 35,400 cycles against 29,780 available — the handler overruns by ~19 %, so exactly one NMI
> is lost. And 35,400 < 2 × 29,780, so never two.**

That is precisely what the dump shows: 17 loads, 17 lag frames, exactly one each.

## 4. Verdict — irreducible, with margin

The overrun is **~5,600 cycles**. Everything that could vary is far too small to close it:

- **`InitializeMemory`'s Y argument** is the only parameter, it is a compile-time constant ($4B
  here), and even setting it to 0 would save just 76 × 18 = **1,368 cycles**. The pages-6-to-0
  sweep is unconditional.
- **The NMI prologue** varies only through `SoundEngine` (what music/SFX is playing) and
  `UpdateScreen` (the VRAM buffer, empty at a load) — a few hundred cycles at most. Note the
  sprite-0 busy-waits (`Sprite0Clr` / `Sprite0Hit`) are already **skipped** at a load, because
  `ChgAreaMode` clears `Sprite0HitDetectFlag`; that path is not available to shorten.
- **Nothing is input-, position-, RNG- or route-dependent.** Consistent with the data: the 17 lag
  frames occur at ITC phases 0…19 and across every level and both entry modes.

**H2 is refuted: the load lag frame cannot be removed.** The prior was right, but it is now a fact
with a cycle count rather than an assumption — and the attribution is corrected from
`InitScreen`/`InitializeNameTables` (which fits comfortably) to `InitializeArea`/`InitializeMemory`
(which does not).

**Residual, stated:** this is a cycle argument from instruction timings, not a measured
cycle count — the harness exposes frames, not cycles. It would be falsified by an emulator trace
showing the handler finishing inside 29,780 cycles, in which case the lag has another cause. The
prediction it makes is sharp and already matches: exactly one lost NMI per load, never zero and
never two, independent of ITC phase, level and entry mode.
