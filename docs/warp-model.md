# SMB1 warp & area-loading model (P0.6) — every player-influenceable table index, from the code

All labels/addresses are from `data/disasm/smbdis.asm` (doppelganger). ROM bytes and OOB reads
come from `tools/warp_tables.py` (pattern-located tables, prints every lookup); enemy/level data
decodes from `tools/area_data.py`; dump evidence from `tools/ram_trace.py` on
`data/wr/fceux_wr.ram` (row i = fm2 frame i−1). Experiment write-up:
`docs/experiments/P0.6-warp-model.md`.

## 0. Conclusions (for the route)
1. **Warp destinations are a closed, small set.** WarpZoneControl (WZC, $06D6) can only be
   0, 1, 4, 5 or 6 when a pipe is entered (§5.4, proof). Reachable warps: 1-2 → {4, 3, 2}
   (WZC 4) or {−1, 5, −1} (WZC 1, the Minus World); 4-2 ceiling zone → 5; 4-2 vine /
   wrong-warp zone ($2F) → {8, 7, 6}. **World 8 is reachable only from 4-2's $2F zone**, which
   is exactly what the WR does. No earlier or more direct warp exists in the tables; a shortcut
   past 8-1…8-3 would need memory corruption (H7), not the warp system.
2. **Pipe destinations are fully enumerated** (§3.3). A pipe goes to `AreaPointer`/`EntrancePage`
   as last written by a row-$0E enemy command that matched `WorldNumber`. The complete command
   table shows the only castle-pointing commands are 8-4's own re-entries (pages 1/7/12/16) and
   the Bowser room (page 16) is written only by the water section's command → no "pipe into
   the Bowser room" outside the normal 8-4 route (H13 refuted at table level).
3. **Game completion** = the axe in any castle while `WorldNumber ≥ 7` (`PlayerEndWorld`:
   `cpy #World8 / bcs`). `WorldNumber` is written only by the warp lookup, `PlayerEndWorld`
   (+1 after a castle), `GoContinue` (title-screen continue / world select) and the
   hard-mode/continue paths; none of them can produce 7 before 4-2 without corruption.
4. The **4-2 wrong warp** is a parse-order effect: the page-5-col-4 pipe is entered before the
   page-5-col-15 command (→ coin room $42) has been parsed, so `AreaPointer` still holds $2F
   (written by the page-2-col-1 command for the vine) → the 8-7-6 zone (dump row 7223).
5. Bogus worlds (35 = "−1", 38, 255) are dead ends or unreachable (§6). WZC 3/7 (worlds 255/38)
   are unreachable. World 35 is the NES Minus World: water area $01 whose commands never
   match (3-bit world field vs 35) → infinite loop; dying recomputes the same pointer.

## 1. Identity variables and what survives an area load
| Var | Addr | Written by | Cleared by `InitializeArea`? |
|---|---|---|---|
| WorldNumber | $075F | `GoContinue` (title), `HandlePipeEntry` (warp), `PlayerEndWorld` (+1) | no |
| LevelNumber | $075C | `PlayerEndLevel` (+1 at star-flag task 5), warp (0), `PlayerEndWorld` (0) | no |
| AreaNumber | $0760 | `NextArea` (+1), warp (0), `PlayerEndWorld` (0), `GoContinue` (0) | no |
| AreaPointer | $0750 | `LoadAreaPointer` (tables), `ParseRow0e` (commands), `HandlePipeEntry` (warp) | no |
| EntrancePage | $0751 | `ParseRow0e`, warp (0) | no |
| AltEntranceControl | $0752 | pipe modes (0/1/2), vine/cloud (2/3), `PlayerEntrance` (0 when control starts) | no |
| HalfwayPage | $075B | `PlayerLoseLife`, `NextArea` (0), `Entrance_GameTimerSetup` (0) | no |
| WarpZoneControl | $06D6 | `ScrollLockObject_Warp` (=4/5/6), `WarpZoneObject` (+1) | **yes** |
| ScrollLock | $0723 | lock objects (eor 1), `WarpZoneObject` (0), flagpole (1 then 0) | yes |
| IntervalTimerControl | $077F | `DecTimers` | no (timers cleared are $0780–$07A1) |

`InitializeArea` (every area load, incl. death restarts via `ContinueGame`) calls
`InitializeMemory` with Y = $4B: clears $0000–$074B (skipping the stack $0160–$01FF) and then
$0780–$07A1. Everything at $074C–$07FF except those timers survives.

## 2. AreaPointer → data (`FindAreaPointer`, `GetAreaDataAddrs`)
- `AreaPointer = AreaAddrOffsets[WorldAddrOffsets[WorldNumber] + AreaNumber]`.
  `WorldAddrOffsets` ($9CB4, 8 bytes) = 00 05 0A 0E 13 17 1B 20; `AreaAddrOffsets` ($9CBC,
  36 bytes). Worlds 1, 2, 4, 7 have **five** areas because the pipe-intro scene ($29,
  GroundArea10) is its own area: AreaNumber ≠ LevelNumber after it (F26's 499-row intro).
- Decode: type = bits 6–5 (0 water, 1 ground, 2 underground, 3 castle); low 5 bits + per-type
  base (`EnemyAddrHOffsets` 1F 06 1C 00, `AreaDataHOffsets` 00 03 19 1C) index the address
  tables. Bit 7 is ignored (8-4's command writes $E5 ≡ $65).
- Header byte 1: bits 7–6 game-timer setting, 5–3 `PlayerEntranceCtrl`, 2–0 fg/bg; byte 2:
  7–6 style (3 = cloud override), 5–4 bg scenery, 3–0 terrain.

Full `AreaAddrOffsets` (index: pointer = level): 0 $25 1-1 | 1 $29 intro | 2 $C0 1-2 |
3 $26 1-3 | 4 $60 1-4 | 5 $28 2-1 | 6 $29 intro | 7 $01 2-2 | 8 $27 2-3 | 9 $62 2-4 |
10 $24 3-1 | 11 $35 3-2 | 12 $20 3-3 | 13 $63 3-4 | 14 $22 4-1 | 15 $29 intro | 16 $41 4-2 |
17 $2C 4-3 | 18 $61 4-4 | 19 $2A 5-1 | 20 $31 5-2 | 21 $26 5-3 | 22 $62 5-4 | 23 $2E 6-1 |
24 $23 6-2 | 25 $2D 6-3 | 26 $60 6-4 | 27 $33 7-1 | 28 $29 intro | 29 $01 7-2 | 30 $27 7-3 |
31 $64 7-4 | 32 $30 8-1 | 33 $32 8-2 | 34 $21 8-3 | 35 $65 8-4.
Sub-areas (never in this table): $42 coin room, $2B/$34 cloud rooms, $00 water bonus, $02 8-4
water, $2F 4-2 warp zone (GroundArea16); $25 page 11 = the flagpole exit of 1-2 and 4-2 (it
is 1-1's data); the coin room's 1-2 section exits to $40 ≡ $C0 (1-2) page 7. Ground pointer
$20+n = GroundArea(n+1); underground $40+n = UndergroundArea(n+1); castle $60+n = CastleArea(n+1).

## 3. When AreaPointer / EntrancePage change
### 3.1 Table recomputation (`LoadAreaPointer`)
`StartWorld1` (Start on the title), `NextArea` (after a flag level or castle: AreaNumber++),
`PlayerEndWorld` (after a castle with WorldNumber < 7: WorldNumber++, Area/Level = 0),
`ContinueGame` (after `PlayerLoseLife` or a Game-Over continue). So a death in a sub-area
always returns to the table area (at `HalfwayPage` if the screen had reached it).

### 3.2 Row-$0E enemy commands (`ParseRow0e`)
Three-byte objects in the enemy data: b0 = column/row $E, b1 = new AreaPointer, b2 = world
(3 bits) <<5 | entrance page (5 bits). Parsed when the enemy parser reaches the column
(column ≤ ScreenRight + 48 px, i.e. about one screen + 3 columns ahead of the left edge) and
**only if the 3-bit world equals WorldNumber** (this is how bonus areas are shared). The write
persists until the next matching command or a table recomputation; it is not tied to a pipe.

### 3.3 Complete command table (`tools/area_data.py` over every `E_*` block)
| Area (pointer) | page:col → AreaPointer, entrance page (world) |
|---|---|
| 1-1 $25 (GroundArea6) | 1:1 → $42 p0 (w1) |
| 1-2 $C0 (Underground1) | 2:13 → $42 p2 (w1); 10:14 → $25 p11 (w1) |
| 2-1 $28 (Ground9) | 3:15 → $2B p0 (w2); 6:15 → $42 p0 (w2) |
| 2-2/7-2 $01 (Water2) | 1:2 → $25 p11 (w2); 1:2 → $25 p11 (w3); 1:4 → $25 p11 (w7) |
| 3-1 $24 (Ground5) | 1:14 → $42 p4 (w3); 7:15 → $34 p0 (w3) |
| 3-3 $20 (Ground1) | — |
| 4-1 $22 (Ground3) | 1:2 → $42 p6 (w4) |
| 4-2 $41 (Underground2) | 2:1 → $2F p0 (w4); 5:15 → $42 p8 (w4); 11:14 → $25 p11 (w4) |
| 5-1 $2A (Ground11) | 9:14 → $42 p8 (w5) |
| 5-2 $31 (Ground18) | 1:10 → $00 p0 (w5); 5:4 → $2B p0 (w5) |
| 6-2 $23 (Ground4) | 1:0 → $42 p8 (w6); 3:13 → $00 p0 (w6); 5:3 → $34 p0 (w6); 7:7 → $42 p6 (w6) |
| 7-1 $33 (Ground20) | 1:13 → $42 p0 (w7) |
| 6-1 $2E / 6-3 $2D / 7-3 $27 / 5-3 $26 / 3-2 $35 / 4-3 $2C | — |
| 8-1 $30 (Ground17) | 1:13 → $42 p2 (w8) |
| 8-2 $32 (Ground19) | 7:15 → $42 p8 (w8) |
| 8-3 $21 (Ground2) | — |
| 8-4 $65 (Castle6) | 3:8 → $65 p1; 5:3 → $65 p7; 8:5 → $65 p1; 9:15 → $65 p12; 13:4 → $65 p1; 14:4 → $02 p0; 17:15 → $65 p1 (all w8) |
| 8-4 water $02 (Water3) | 4:2 → $65 p16 (w8) |
| water bonus $00 (Water1) | 1:14 → $31 p7 (w5); 1:14 → $23 p7 (w6) |
| coin room $42 (Underground3) | 1:1 → $25 p10 (w1); 1:2 → $28 p7 (w2); 1:2 → $33 p7 (w7); 3:1 → $40 p7 (w1); 3:2 → $30 p7 (w8); 5:1 → $24 p4 (w3); 7:1 → $22 p10 (w4); 7:2 → $23 p11 (w6); 9:1 → $41 p8 (w4); 9:1 → $2A p10 (w5); 9:2 → $23 p2 (w6); 9:2 → $32 p10 (w8) |
| cloud $2B (Ground12) | 1:0 → $28 p10 (w2); 1:0 → $31 p8 (w5) |
| cloud $34 (Ground21) | 1:0 → $24 p10 (w3); 1:1 → $23 p10 (w6) |
| 4-2 warp zone $2F (Ground16) | — (enemy data is empty: one $FF) |
(Worlds are shown 1-based as displayed; the byte holds WorldNumber = world − 1.)

WR 8-4 room loads (dump lag rows): 15798 $E5 p7, 16235 $65 p12, 16600 $02 p0, 17470 $65 p16
(Bowser room) — all `AltEntranceControl = 2`, unquantized (F28).

### 3.4 Warp pipes (`HandlePipeEntry`, smbdis.asm ~12270)
Down held, right-foot metatile $11 and left-foot $10 → `ChangeAreaTimer = $30`, GES = 3,
then **if WZC ≠ 0**: index = (WZC & 3)·4 + {0 if X < $60, 1 if X < $A0, else 2} into
`WarpZoneNumbers` ($87F2); `WorldNumber = byte − 1`; `AreaPointer =
AreaAddrOffsets[WorldAddrOffsets[WorldNumber]]`; EntrancePage = AreaNumber = LevelNumber =
AltEntranceControl = 0; `FetchNewGameTimerFlag` set. `VerticalPipeEntry` then picks the entry
mode: WZC ≠ 0 → 0 (main-level entry with intermission card → framerule-quantized, F28);
castle → 2; otherwise 1 (sub-area, unquantized). Side pipes (`SideExitPipeEntry`) always use
mode 2 and never consult WZC. Vines: `Vine_AutoClimb` → mode 2; cloud-area fall-out → mode 3.

## 4. Player entrance (`Entrance_GameTimerSetup`, `PlayerEntrance`)
`PlayerStarting_X_Pos[AltEntranceControl]` (4 entries), `PlayerStarting_Y_Pos[x]` (9 entries,
x = `PlayerEntranceCtrl` 0–7 from the header, or `AltYPosOffset[mode−2]` for modes 2/3),
`PlayerBGPriorityData[x]` (8). Header bits are 3 wide, modes are 0–3: all in bounds — no OOB
here. `HalfwayPage` overrides the header entrance (`PlayerEntranceCtrl = 2`) on a restart.
Mode 2 (`EntrMode2`) rises Mario 1 px/frame until Y < $91 (the 96-frame pipe exit of F33).

## 5. Warp zones
### 5.1 The three objects
- `ScrollLockObject_Warp` (area object, row 13 id $45): WZC = 4 if WorldNumber = 0, else 5,
  else **6 if AreaType = ground** (1-2: 4; 4-2 ceiling zone, underground type: 5; $2F zone,
  ground type: 6). Prints the text and the three numbers, kills piranha plants, then toggles
  `ScrollLock` (eor 1).
- `ScrollLockObject` (row 13 id $46/$47): toggles `ScrollLock`.
- `WarpZoneObject` (enemy id $34, runs via `RunEnemyObjectsCore` index $34−$14): every frame
  while alive: if `ScrollLock ≠ 0` and `(Player_Y & Player_Y_HighPos) = 0` → ScrollLock = 0,
  **WZC += 1**, erase self (`EraseEnemyObject`). With HighPos 1 this means Mario's Y even;
  with HighPos 0 (above the screen) always.
### 5.2 Layouts (`tools/area_data.py`)
| Zone | lock | enemy $34 | pipes (warp, d3) | text ($45) |
|---|---|---|---|---|
| 1-2 ($C0) | 11:2 | 11:2 row 7 | 11:2, 11:6, 11:10 | 12:6 |
| 4-2 ceiling ($41, pages 12–14) | 12:4 | 11:8 row 7 | 13:6 (one pipe) | 14:6 |
| 4-2 vine/wrong warp ($2F) | — | — (no enemies) | 3:2, 3:6, 3:10 | 4:6 |
### 5.3 Dump evidence (`tools/ram_trace.py`)
1-2: enemy $34 in slot 2 from row 3471; row 3545 lock parsed (ScrollLock 1; screen page 9,
Mario page 10 X 50); row 3546 enemy fires (ScrollLock 0, WZC 1, slot erased; Y = 116 even);
row 3721 text (WZC 4, ScrollLock 1). 4-2: pipe at page 5 taken with AreaPointer $2F → load at
row 7223 (mode 1); in $2F the text fires at row 7608 (WZC 6, ScrollLock 1, screen page 3);
pipe entered at row 7724 with X = 114 (< $60 → left) → WorldNumber 7, AreaPointer $30 (8-1).
No $34 object ever exists in the $2F zone (E_GroundArea16 is empty).
### 5.4 Reachable WZC values — proof that WZC ∈ {0, 1, 4, 5, 6}
(a) WZC is cleared on every area load (§1) and written only by the text object (absolute
4/5/6) and the enemy (+1). (b) Enemy id $34 comes only from enemy data (the only other
`Enemy_ID` writers are data-driven group/cheep/buzzy/Bowser-replacement paths and the vine/
frenzy queues with fixed ids); each zone has at most one, it is never re-parsed (the enemy data
offset only advances; `ExecGameLoopback` exists only in 4-4/7-4/8-4), and it erases itself when
it fires → at most one +1 per area visit. (c) The +1 cannot come after the text: the text
object is parsed only when the renderer reaches its column, the renderer advances only while
the screen scrolls (`UpdScrollVar`: parser tasks are queued by 32-px scroll steps), and
scrolling is blocked while `ScrollLock = 1` (`ScrollHandler`). The lock object precedes the
text by 20 (1-2) / 34 (4-2) columns, and `ScrollLock` is cleared only by the enemy firing, by
a second lock object (needs scrolling) or by the flagpole (none in these areas). So the enemy
must fire (WZC 0→1) before the text (WZC := 4/5) can run, and in $2F there is no enemy at all.
Hence per visit the sequence is 0 → (1) → 4/5/6 and a pipe sees 0, 1, 4, 5 or 6. Values 2, 3,
7 (and WorldNumber 255/38) are unreachable. **H5 refuted.**
### 5.5 Destination table (`tools/warp_tables.py`)
| WZC & 3 | X < $60 | $60 ≤ X < $A0 | X ≥ $A0 |
|---|---|---|---|
| 0 (WZC 4, 1-2 after text) | 4 (→ $22 4-1) | 3 (→ $24 3-1) | 2 (→ $28 2-1) |
| 1 (WZC 1 or 5) | 36 = "−1" (WorldNumber 35 → $01 Water2) | 5 (→ $2A 5-1) | 36 |
| 2 (WZC 6, $2F zone) | 8 (→ $30 8-1) | 7 (→ $33 7-1) | 6 (→ $2E 6-1) |
| 3 (WZC 3/7, unreachable) | 0 (WorldNumber 255 → $9D) | 0 (255) | 39 (WorldNumber 38 → $00) |
In the 4-2 ceiling zone the single pipe sits at columns 6–7 (X $60–$7F) → middle → 5 whether
WZC is 1 or 5. In 1-2 a pipe taken between the enemy and the text (WZC 1) gives the Minus
World (left/right) or 5-1 (middle); after the text, 4/3/2. With WZC 0 (before the enemy fires,
or any pipe in $2F before its text) the pipe is an ordinary pipe → `AreaPointer`: in $2F that
is $2F itself (re-enter the zone at page 0, mode 1) — a loop that costs a load.

## 6. Bogus worlds (`tools/warp_tables.py`, "FindAreaPointer for the bogus worlds")
- **35 ("−1", reachable):** `WorldAddrOffsets[35]` = `AreaAddrOffsets[27]` = $33 →
  `AreaAddrOffsets[51]` = `EnemyDataAddrLow[11]` = $01 = Water2 (2-2/7-2 data). Its three
  commands require world 2/3/7 → never match 35 → the exit pipe reloads $01 at EntrancePage 0.
  Death: `HalfwayPageNybbles[70/71]` = $4A/$29 → nybble 4 or 9 vs ScreenLeft page → restart
  page; `ContinueGame` → `FindAreaPointer` → $01 again. Game over → `ContinueWorld` = 35 →
  A+Start → `GoContinue` → same. No flagpole (Water2 has none) → no `NextArea`. Closed loop at
  the table level; only memory corruption (H7) could leave it. Areas 1–5 of world 35 would be
  $1F/$3C/$51/$7B/$7C (garbage pointers) but `AreaNumber` never increments there.
- **38 and 255 (unreachable, WZC 3/7):** 38 → $00 (water bonus, commands for worlds 5/6 only);
  255 → `WorldAddrOffsets[255]` = $4C → `AreaAddrOffsets[76]` = $9D: water type, enemy data
  address $7EA0 = unmapped on NROM (open bus: emulator-defined), level data $A210.
  `BowserIdentities[38/255]` = $CE/$A9, `Hidden1UpCoinAmts`, `HalfwayPageNybbles[76..]` = $F0…
  — listed for P3.1 but moot.

## 7. Other WorldNumber / id-indexed tables (all reads, with bounds)
| Table | Index | Size | In-bounds for reachable values? |
|---|---|---|---|
| `WorldAddrOffsets` | WorldNumber | 8 | only for 0–7 (35 → $33, see §6) |
| `HalfwayPageNybbles` | 2·World (+1 for -3/-4) | 16 | 0–7 yes |
| `Hidden1UpCoinAmts` | WorldNumber | 8 | yes (35 → $04) |
| `BowserIdentities` | WorldNumber (Bowser killed by fire) | 8 | yes; 35 → $2D (Bowser again) |
| `LoopCmd*` | loop slot, compared with WorldNumber 3/6/7 | 11 | n/a (compare only) |
| `InitEnemyRoutines` | Enemy_ID | 47 ($00–$2E) | data ids are 6-bit; ≥ $37 are group objects, $3F would be OOB but no area's data contains $3C–$3F (`tools/area_data.py` scan) |
| `RunEnemyObjectsCore` | Enemy_ID − $14 (ids ≥ $15) | 34 ($15–$35) | yes for all ids the code writes |
| `WarpZoneNumbers` | (WZC&3)·4 + pipe | 12 | yes for WZC ∈ {0,1,4,5,6} |
| `PlayerStarting_*`, `PlayerBGPriorityData`, `GameTimerData` | header bits / AltEntranceControl | 4/9/8/4 | yes |
Bowser by world (`RunBowser`): hammers from world 6 (WorldNumber ≥ 5), flames only in world 8
or worlds < 6; `BowserIdentities[WorldNumber]` replaces a fire-killed Bowser (Goomba … Bowser).
The ending: world 8 → princess message path; `PlayerEndWorld` ends the game for
WorldNumber ≥ 7, else WorldNumber++ and 1 of the next world (via `LoadAreaPointer`).

## 8. Boot (`Start`)
Warm boot iff all six `TopScoreDisplay` digits ($07D7–$07DC) < 10 **and**
`WarmBootValidation` ($07FF) = $A5; then only $0000–$07D5 is cleared (keeps top score,
`WorldSelectEnableFlag` $07FC, `ContinueWorld` $07FD, the validation byte). Power-on → cold
boot (clears $0000–$07FD… i.e. up to `ColdBootOffset` $07FE) and writes $A5 to $07FF. The
title screen's A+Start continue reads `ContinueWorld`, which is written only by
`TerminateGame` (game over) — 0 on a fresh power-on; world select needs `WorldSelectEnableFlag`
(set only by the ending). So without a reset there is nothing to exploit at boot; with a reset
(H15, rules permitting) the continue would cost a game over first.

## 9. Hypotheses touched
H5 refuted (§5.4); H6 refuted at table level (§6; corruption path folded into H7); H13 refuted
at table level (§3.3; the only castle-page writer is 8-4's own water command); H14 untouched
(vines: `Vine_AutoClimb` mode 2 into `AreaPointer` at `EntrancePage` — same table); H15
annotated (§8); H7 gains a concrete target: `WorldNumber` ($075F) ≥ 7 before any castle's axe,
or `AreaPointer`/`EntrancePage` ($0750/$0751) = $65/16 before an 8-x pipe.
