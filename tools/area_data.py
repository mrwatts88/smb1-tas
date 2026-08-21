#!/usr/bin/env python3
"""Decode SMB1 enemy-object data for an area from the disassembly (data/disasm/smbdis.asm).

Usage: tools/area_data.py E_UndergroundArea2 L_UndergroundArea2 [more labels]  (E_ = enemies, L_ = area objects)
Format (ProcessEnemyData, smbdis.asm): 2-byte objects  b0 = column<<4 | row, b1 = next-page<<7 |
hard-mode<<6 | id; row $0F = page-skip (b1 & $3F = new page); row $0E = 3-byte area-change command
(b1 = new AreaPointer, b2 = world<<5 | entrance page; honoured only when world == WorldNumber).
Absolute page is tracked the way EnemyObjectPageLoc is (starts at 0, +1 on the next-page bit).
"""
import re
import sys

DISASM = "data/disasm/smbdis.asm"

def read_block(label):
    lines = open(DISASM, encoding="utf-8", errors="replace").read().split("\n")
    out, on = [], False
    for ln in lines:
        if re.match(rf"^{re.escape(label)}:\s*$", ln):
            on = True
            continue
        if on:
            m = re.match(r"^\s*\.db\s+(.*)$", ln)
            if m:
                out += [int(t.strip()[1:], 16) for t in m.group(1).split(";")[0].split(",") if t.strip()]
            elif ln.strip() and not ln.strip().startswith(";"):
                break
    if not out:
        raise SystemExit(f"label {label} not found")
    return out

def decode(label):
    b = read_block(label)
    print(f"{label}: {len(b)} bytes")
    i, page, page_sel = 0, 0, False
    while i < len(b) and b[i] != 0xFF:
        row, col = b[i] & 0x0F, b[i] >> 4
        if row == 0x0F:
            page = b[i + 1] & 0x3F
            print(f"  +{i:3d}: page-skip -> page {page}")
            i += 2
            continue
        if b[i + 1] & 0x80:
            page += 1
        if row == 0x0E:
            ap, w, ep = b[i + 1] & 0x7F, b[i + 2] >> 5, b[i + 2] & 0x1F
            print(f"  +{i:3d}: page {page:2d} col {col:2d}  AREA-CHANGE -> AreaPointer ${ap:02X} "
                  f"entrance page {ep} (only if WorldNumber == {w})")
            i += 3
            continue
        eid, hard = b[i + 1] & 0x3F, (b[i + 1] >> 6) & 1
        print(f"  +{i:3d}: page {page:2d} col {col:2d} row {row:2d}  id ${eid:02X}{' hard-only' if hard else ''}")
        i += 2
    print("  end")

ROW13 = ["IntroPipe", "FlagpoleObject", "AxeObj", "ChainObj", "CastleBridgeObj", "ScrollLockObject_Warp",
         "ScrollLockObject", "ScrollLockObject", "AreaFrenzy(flying cheeps)", "AreaFrenzy(bullets/cheeps)",
         "AreaFrenzy(stop)", "LoopCmd"]
ROW12 = ["Hole_Empty", "PulleyRope", "Bridge_High", "Bridge_Middle", "Bridge_Low", "Hole_Water",
         "QBlockRow_High", "QBlockRow_Low"]
ROW15 = ["EndlessRope", "BalancePlatRope", "CastleObject", "Staircase", "ExitPipe", "FlagBalls"]
LARGE = ["VerticalPipe(warp, d3 set)", "AreaStyleObject", "RowOfBricks", "RowOfSolidBlocks", "RowOfCoins",
         "ColumnOfBricks", "ColumnOfSolidBlocks", "VerticalPipe(decoration)"]
SMALL = ["QBlock power-up", "QBlock coin", "hidden coin", "hidden 1-up", "brick power-up", "brick vine",
         "brick star", "brick coins", "brick 1-up", "WaterPipe", "EmptyBlock", "Jumpspring"]

def decode_area(label):
    """Area-object (level) data: 2-byte header, then 2-byte objects (ProcessAreaData/DecodeAreaData)."""
    b = read_block(label)
    h0, h1 = b[0], b[1]
    print(f"{label}: {len(b)} bytes; header timer {h0 >> 6} entrance {(h0 >> 3) & 7} fg/bg {h0 & 7}; "
          f"bg-scenery {(h1 >> 4) & 3} terrain {h1 & 15} style {h1 >> 6}")
    i, page = 2, 0
    while i < len(b) and b[i] != 0xFD:
        col, row, b2 = b[i] >> 4, b[i] & 0x0F, b[i + 1]
        if b2 & 0x80:
            page += 1
        if row == 13 and not (b2 & 0x40):
            page = b2 & 0x1F
            print(f"  +{i:3d}: page-control -> page {page}")
        elif row == 13:
            k = b2 & 0x3F
            print(f"  +{i:3d}: page {page:2d} col {col:2d} row 13  {ROW13[k] if k < len(ROW13) else f'?{k}'}")
        elif row == 14:
            print(f"  +{i:3d}: page {page:2d} col {col:2d} row 14  AlterAreaAttributes ${b2 & 0x7F:02X}")
        elif row == 12:
            print(f"  +{i:3d}: page {page:2d} col {col:2d} row 12  {ROW12[(b2 >> 4) & 7]} len {b2 & 15}")
        elif row == 15:
            print(f"  +{i:3d}: page {page:2d} col {col:2d} row 15  {ROW15[(b2 >> 4) & 7]} len {b2 & 15}")
        else:
            t = (b2 >> 4) & 7
            if t == 0:
                print(f"  +{i:3d}: page {page:2d} col {col:2d} row {row:2d}  {SMALL[b2 & 15]}")
            else:
                warp = t == 7 and (b2 & 8)
                print(f"  +{i:3d}: page {page:2d} col {col:2d} row {row:2d}  {LARGE[0] if warp else LARGE[t]} len {b2 & 7 if t == 7 else b2 & 15}")
        i += 2
    print("  end")

for lab in sys.argv[1:]:
    (decode_area if lab.startswith("L_") else decode)(lab)
