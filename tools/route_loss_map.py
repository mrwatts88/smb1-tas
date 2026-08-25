#!/usr/bin/env python3
"""E9a - where the WR route loses speed, and what geometry is next to it.

A walk-through (F80/F239) only buys frames where the route is NOT at the movement cap: at the
cap the wall costs nothing (SMB1's airborne x-speed cap equals the ground cap, so clearing a
short obstacle by jumping is free).  This joins the cap survey (F225) to the block maps: every
contiguous off-cap run of control frames, with the columns/rows Mario's collision probes were
in, the blocking cells around him, and whether a side collision fired.

Usage: tools/route_loss_map.py [--ram FILE] [--min N] [--area TAG]
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from route_blockmaps import ROUTE          # noqa: E402
from wall_face_census import blocking, cls, load_grid, probe_rows   # noqa: E402

RAM = 0x800
P_X, P_PAGE, P_Y, P_SPD, P_STATE, P_YHI, GES = 0x86, 0x6d, 0xce, 0x57, 0x1d, 0xb5, 0x0e
P_SIZE, P_CROUCH, SIDE_TIMER = 0x0754, 0x0714, 0x0709

def main():
    ram = sys.argv[sys.argv.index("--ram") + 1] if "--ram" in sys.argv else "data/wr/fceux_wr.ram"
    minlen = int(sys.argv[sys.argv.index("--min") + 1]) if "--min" in sys.argv else 4
    only = sys.argv[sys.argv.index("--area") + 1] if "--area" in sys.argv else None
    data = open(ram, "rb").read()
    B = lambda i, a: data[(i - 1) * RAM + a]
    S = lambda i: (lambda v: v - 256 if v > 127 else v)(B(i, P_SPD))
    total_off = 0
    print("off-cap runs of WR control frames (cap = |x_spd| in {40,24}); "
          "'wall' = blocking cell at the side probe row within 2 columns ahead\n")
    for tag, name, label, ranges in ROUTE:
        if only and tag != only:
            continue
        grid = load_grid(tag)
        if grid is None:
            continue
        rows = [i for first, last in ranges for i in range(first, last + 1)]
        off = [i for i in rows if B(i, GES) == 8 and B(i, P_YHI) == 1 and abs(S(i)) not in (40, 24)]
        # contiguous
        runs, s, prev = [], None, None
        for i in off:
            if s is None:
                s = i
            elif i != prev + 1:
                runs.append((s, prev))
                s = i
            prev = i
        if s is not None:
            runs.append((s, prev))
        ctrl = sum(1 for i in rows if B(i, GES) == 8 and B(i, P_YHI) == 1)
        total_off += len(off)
        print(f"## {tag}  {name}: {len(off)} off-cap of {ctrl} control frames "
              f"({100*len(off)/max(1,ctrl):.0f}%), {len(runs)} runs")
        for a, b in sorted(runs, key=lambda t: -(t[1] - t[0]))[:12]:
            if b - a + 1 < minlen:
                continue
            xs = [B(i, P_PAGE) * 256 + B(i, P_X) for i in range(a, b + 1)]
            ys = [B(i, P_Y) for i in range(a, b + 1)]
            sp = [S(i) for i in range(a, b + 1)]
            sm = B(a, P_SIZE) != 0 or B(a, P_CROUCH) != 0
            rs = sorted({r for i in range(a, b + 1) for r in probe_rows(B(i, P_Y), sm)})
            sidehit = sum(1 for i in range(a, b + 1) if B(i, SIDE_TIMER) != 0)
            walls = set()
            for i in range(a, b + 1):
                ax = B(i, P_PAGE) * 256 + B(i, P_X)
                for r in probe_rows(B(i, P_Y), sm):
                    for dc in (0, 1, 2):
                        c = ((ax + 13) >> 4) + dc
                        if 0 <= r < 13 and c < len(grid[0]) and blocking(grid[r][c]):
                            walls.add((r, c, grid[r][c]))
            print(f"  rows {a}-{b} ({b-a+1:3d} f)  x {min(xs):4d}->{max(xs):4d} (col {min(xs)//16:3d}-{max(xs)//16:3d})"
                  f"  y {min(ys):3d}-{max(ys):3d}  spd {sp[0]:+3d}->{sp[-1]:+3d} min {min(sp):+3d}"
                  f"  proberows {rs}  sidecoll {sidehit}f")
            if walls:
                print("      blocking ahead: " +
                      " ".join(f"(r{r},c{c},{m:#04x} {cls(m)})" for r, c, m in sorted(walls)[:10]))
        print()
    print(f"TOTAL off-cap control frames on the route: {total_off}")

if __name__ == "__main__":
    main()
