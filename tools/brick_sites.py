#!/usr/bin/env python3
"""Big-Mario pricing aid: print the metatiles around each geometric-loss site of the WR (F245) and class
each cell by what a head hit does to it (smbdis 11946-11973, 7219-7287, 7361-7375, 12355-12361):
  .  empty ($00)          B  breakable by big Mario (head-bumpable and not an item block)
  Q  item/coin block (bumps, never breaks)       #  solid to the head (>= SolidMTileUpperExt of its group)
  c  coin ($c2/$c3)
usage: tools/brick_sites.py [TAG C0 C1]...   (no args: the seven F245 sites)"""
import sys
SOLID = [0x10, 0x61, 0x88, 0xc4]
ITEM = {0xc1, 0xc0, 0x5f, 0x60, 0x55, 0x56, 0x57, 0x58, 0x59, 0x5a, 0x5b, 0x5c, 0x5d, 0x5e}
def cls(m):
    if m == 0: return "."
    if m in (0xc2, 0xc3): return "c"
    if m >= SOLID[m >> 6]: return "#"
    return "Q" if m in ITEM else "B"
def grid(tag):
    return [[int(v, 16) for v in line.split()] for line in open(f"data/blockmaps/{tag}.grid") if line.strip()]
SITES = [("w82", 197, 214, "114 f"), ("w84r3", 210, 219, "38 f"), ("w42m", 20, 36, "33 f (the mint)"),
         ("w12", 160, 174, "33 f (the clip)"), ("w42w", 54, 62, "30 f"), ("w12", 179, 187, "27 f"),
         ("w84r2", 147, 155, "15 f")]
a = sys.argv[1:]
if a: SITES = [(a[i], int(a[i + 1]), int(a[i + 2]), "") for i in range(0, len(a), 3)]
for tag, c0, c1, note in SITES:
    g = grid(tag); c1 = min(c1, len(g[0]) - 1)
    print(f"\n{tag} cols {c0}-{c1}  {note}")
    print("row  " + " ".join(f"{c:3d}" for c in range(c0, c1 + 1)))
    for r, row in enumerate(g):
        print(f"{r:3d}  " + " ".join(f" {cls(row[c])}{row[c]:02x}" if row[c] else "  . " for c in range(c0, c1 + 1)))
    n = sum(cls(row[c]) == "B" for row in g for c in range(c0, c1 + 1))
    print(f"  breakable cells in window: {n}")
