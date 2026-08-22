# Static out-of-bounds audit (P3.1) — indexed stores and jumps whose index the player can influence

Tool: `tools/oob_audit.py` (scans `data/disasm/smbdis.asm`).
- `--target $ADDR`: every store `base,x` / `base,y` whose absolute base lies ≤ 255 bytes below ADDR (the
  6502 reach of absolute-indexed addressing), with the index value needed and the index register's last
  setter in the routine; zero-page bases are excluded for targets ≥ $100 (ZP-indexed wraps inside the ZP);
  `(zp),y` pointer stores are listed separately (their base is dynamic).
- default / `--writes --player --symbol --routine`: the full table of indexed accesses with provenance.
Counts: 1,527 indexed accesses, 732 stores, 8 pointer stores (`(zp),y`), 18 `JumpEngine` call sites.

## 1. H7 targets: $075F WorldNumber, $0750 AreaPointer, $0751 EntrancePage, $06D6 WarpZoneControl
Absolute-indexed stores in reach (same set for all four, different index values): `MetatileBuffer,x/y`
($06A1/$06A2; index = the column-render row from `$07` / loop counters, ≤ 15, in the area parser's
render routines — `SceLoop1/2`, `TerrBChk`, `MidTreeL`, `EndMushL`, `CRendLoop`, `WaterPipe`,
`VPipeSectLoop`, `DrawSidePart`, `DrawPipe`, `QuestionBlockRow_Low`, `Bridge_Low`, `BulletBillCannon`,
`Jumpspring`); `AreaObjectLength,x` / `AreaObjOffsetBuffer,x` / `MushroomLedgeHalfLen,x` (object slots 0–2);
`SavedJoypadBits,x` / `JoypadBitMask,x` (joypad port 0–1); `Misc_SprDataOffset`, `SprDataOffset,x`
(sprite-shuffler offsets ≤ 14); `HammerEnemyOffset,y` (hammer slots); `Misc_Collision_Flag,x`
(`ObjectOffset` ≤ 5); `OnscreenPlayerInfo,x` with index 5 = $075F — **by design** (the 2-player
`TransposePlayers` copy of the 8-byte player block; WorldNumber is part of it). The needed indices
(21…190) are impossible for every one of these: each index is a nibble (row/column), a slot number or a
port number, bounded by construction (read: routines above). **Verdict: no absolute-indexed store can
reach the four cells.**

## 2. Pointer stores `sta (zp),y` (8 sites)
- `($06),y` = the **block buffer** pointer (`GetBlockBufferAddr`, 4328): $07 = $05, $06 = {$00 | $D0}[page
  LSB] + column (0–15); y = ((Y + adder) & $F0) − $20 = 16·row. Sites: `StrBlock` 3282 (area parser),
  `VineObjectHandler` 6754 (writes $26 where the vine grows), `PutMTileB` 7262 / 7517 (block bumps), 7408
  (coin removal), `ErACM` 12136 (`HandleClimbing`/coin erase), `HandleEToBGCollision` 12443 (enemy hits a
  block from below), `CheckTopOfBlock`-area 7404. **Out-of-bounds case:** an object above the status bar
  (Y + adder < $20) makes y wrap to $E0 or $F0, so the write lands at base + column + $E0/$F0: from
  Block_Buffer_1 ($0500) into Block_Buffer_2 ($05E0–$05FF, harmless), from Block_Buffer_2 ($05D0) into
  **$06B0–$06CF**: `JumpCoinMiscOffset` $06B7, `BrickCoinTimerFlag` $06BC, `Misc_Collision_Flag` $06BE,
  **`EnemyFrenzyBuffer` $06CB** (column 11, y $F0), **`SecondaryHardMode` $06CC** (column 12),
  `EnemyFrenzyQueue` $06CD, `FireballCounter` $06CE, `DuplicateObj_Offset` $06CF. Maximum reach $06CF —
  **$06D6/$0750/$0751/$075F are unreachable** through the block buffer. But a value written into
  `EnemyFrenzyBuffer` is consumed by `InitEnemyFrenzy` (8835: `sbc #$12`, `JumpEngine` with **6** entries):
  a vine metatile $26 there gives index 20 → a jump through bytes past the table (H30, for P3.3 on the core).
- `($00),y` `OutputTScr` (title-screen VRAM) and `InitByte` (`InitializeMemory`, 2779): engine-internal,
  fixed pointers.

## 3. `JumpEngine` call sites (18) — index provenance
All indices are engine state (`OperMode`, `OperMode_Task`, `ScreenRoutineTask`, `GameEngineSubroutine` 13
entries for GES 0–12, `Player_State` 0–3, `AreaStyle` 0–2, `StarFlagTaskControl` < 5, block-object type
< 9, area-object type from ROM level data) or `Enemy_ID`: `EnemyMovementSubs` (21 entries, only for IDs
< $15 by `RunEnemyObjectsCore`'s guard), `JmpEO` (34 entries for IDs $15–$36), `LargePlatformSubroutines`
(IDs $24–$2A), `InitEnemyRoutines` (55 entries, IDs ≤ $36), `InitEnemyFrenzy` (6 entries, IDs $12–$17 from
`FrenzyIDData`). `Enemy_ID` writers are level data (ROM, IDs ≤ $3E with the pair codes translated) and
constants (`Setup_Vine` $2F, `PowerUpObject` $2E, flag/fireworks/Bowser identities) — **except the
`EnemyFrenzyBuffer` path above**, the only way a computed byte becomes a jump index.

## 4. Verdict and what remains
- The H7 cells ($075F, $0750/$0751, $06D6) cannot be written by any indexed or pointer store with a
  player-influenceable index; they change only through the game's own transitions (P0.6 warp model).
- One genuine OOB-write mechanism exists (block-buffer writes for objects above the status bar) with a
  bounded reach $05E0–$06CF; its interesting cell is `EnemyFrenzyBuffer` (→ `JumpEngine` index out of range
  = a code-execution candidate) and `SecondaryHardMode`. The vine is the natural writer (it grows to the
  top of the screen by design); block bumps/coin erases need Mario or an enemy above Y $20. → H30, P3.3.
- Not covered here: stack overflow/underflow paths, non-indexed writes (by design), VRAM-buffer overflows
  (`VRAM_Buffer` writes indexed by `VRAM_Buffer1_Offset` — a classic corruption vector in other games; the
  offsets here are bounded by the parser's row counts, not audited line by line).

## 5. Vine positions (H30 check)
`tools/area_data.py L_*`: brick-vine objects at GroundArea4 page 5 col 1, GroundArea5 page 8 col 3,
GroundArea9 page 5 col 3, GroundArea18 page 5 col 5, UndergroundArea2 page 4 col 0. Odd pages (Block_Buffer_2)
with columns 1/3/5 → the wrapped vine writes land at $06B1/$06C1, $06B3/$06C3, $06B5/$06C5 (no named RAM);
even pages → inside Block_Buffer_2. So no vine reaches `EnemyFrenzyBuffer` ($06CB) or `SecondaryHardMode`
($06CC): H30's vine variant is refuted by the level data. The mechanism remains the only OOB write in the
game; a different writer above Y $20 at an odd-page column 11/12 would be needed.
