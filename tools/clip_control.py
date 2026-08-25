#!/usr/bin/env python3
"""POSITIVE CONTROL for the E9a census: find every frame of the WR where Mario is actually INSIDE
terrain, and check the census classifier calls it possible.

A census that cannot reproduce clips that demonstrably happen is worthless.  Ground truth here is
HappyLee's own run: it contains 4-2's wall walk (F80/F239), 1-2's clip (F143/F144) and 8-4's pipe
clips (F66) -- all publicly known.  For every control frame we recompute the exact probe cells
(F241) and flag the frames where a probe is inside a blocking cell, i.e. Mario is embedded.  Then
we group them into episodes and print, for each, how he got in.

Usage: tools/clip_control.py [--ram FILE]
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from route_blockmaps import ROUTE                                    # noqa: E402
from wall_face_census import blocking, cls, load_grid, YA_SMALL, YA_BIG  # noqa: E402

RAM = 0x800
P_X, P_PAGE, P_Y, P_SPD, P_STATE, P_YHI, GES = 0x86, 0x6d, 0xce, 0x57, 0x1d, 0xb5, 0x0e
P_SIZE, P_CROUCH, P_MDIR = 0x0754, 0x0714, 0x45

def main():
    ram = sys.argv[sys.argv.index("--ram") + 1] if "--ram" in sys.argv else "data/wr/fceux_wr.ram"
    data = open(ram, "rb").read()
    B = lambda i, a: data[(i - 1) * RAM + a]
    S = lambda i: (lambda v: v - 256 if v > 127 else v)(B(i, P_SPD))
    total = 0
    for tag, name, label, ranges in ROUTE:
        grid = load_grid(tag)
        if grid is None:
            continue
        w = len(grid[0])
        hits = []
        for f, l in ranges:
            for i in range(f, l + 1):
                if B(i, GES) != 8 or B(i, P_YHI) != 1:
                    continue
                y, x, pg = B(i, P_Y), B(i, P_X), B(i, P_PAGE)
                sm = B(i, P_SIZE) != 0 or B(i, P_CROUCH) != 0
                ya = YA_SMALL if sm else YA_BIG
                ax = pg * 256 + x
                emb = []
                for k, xa in ((3, 0x02), (4, 0x02 if sm else 0x02), (5, 0x0d), (6, 0x0d)):
                    r = ((y + ya[k]) & 0xF0) // 16 - 2
                    c = (ax + xa) >> 4
                    if 0 <= r < 13 and 0 <= c < w and blocking(grid[r][c]):
                        emb.append((("L" if xa == 0x02 else "R"), r, c, grid[r][c]))
                if emb:
                    hits.append((i, ax, y, S(i), emb))
        if not hits:
            continue
        # group into episodes (gap > 8 frames)
        eps, cur = [], [hits[0]]
        for h in hits[1:]:
            if h[0] - cur[-1][0] > 8:
                eps.append(cur)
                cur = [h]
            else:
                cur.append(h)
        eps.append(cur)
        print(f"## {tag} {name}: {len(hits)} embedded control frames in {len(eps)} episodes")
        for e in eps:
            total += len(e)
            i0, i1 = e[0][0], e[-1][0]
            xs = [h[1] for h in e]
            rows = sorted({m[1] for h in e for m in h[4]})
            sides = "".join(sorted({m[0] for h in e for m in h[4]}))
            tiles = sorted({m[3] for h in e for m in h[4]})
            spd = [h[3] for h in e]
            pre = i0 - 1
            print(f"  rows {i0}-{i1} ({len(e):3d} f)  x {min(xs)}-{max(xs)}  probe rows {rows} "
                  f"side {sides}  tiles {[hex(t) for t in tiles]}  spd {min(spd)}..{max(spd)}")
            print(f"      entry frame {i0}: x {e[0][1]} y {e[0][2]} spd {e[0][3]} "
                  f"state {B(i0, P_STATE)} MovingDir {B(i0, P_MDIR)} | previous frame: "
                  f"x {B(pre, P_PAGE)*256+B(pre, P_X)} y {B(pre, P_Y)} spd {S(pre)} "
                  f"state {B(pre, P_STATE)} MovingDir {B(pre, P_MDIR)}")
    print(f"\nTOTAL embedded control frames on the WR route: {total}")

if __name__ == "__main__":
    main()
