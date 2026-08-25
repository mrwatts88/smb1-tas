#!/usr/bin/env python3
"""E9a - what each obstacle on the WR route actually costs, in frames.

Merges nearby off-cap runs into one "obstacle window", then prices the window against the
x-only movement bound (2.5 px/frame at the running cap): loss = frames - |dx| / 2.5.  This is
the value column of the wall-face census: a face is only worth a walk-through where the route
is paying frames for the geometry.  Level-start accelerations (the forced ramp after the
intermission card, F225) are marked so they are not mistaken for recoverable geometry.

Usage: tools/route_obstacle_cost.py [--ram FILE] [--gap N] [--min N]
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from route_blockmaps import ROUTE  # noqa: E402

RAM = 0x800
P_X, P_PAGE, P_Y, P_SPD, P_YHI, GES, TASK = 0x86, 0x6d, 0xce, 0x57, 0xb5, 0x0e, 0x0772

def main():
    ram = sys.argv[sys.argv.index("--ram") + 1] if "--ram" in sys.argv else "data/wr/fceux_wr.ram"
    gap = int(sys.argv[sys.argv.index("--gap") + 1]) if "--gap" in sys.argv else 25
    minloss = int(sys.argv[sys.argv.index("--min") + 1]) if "--min" in sys.argv else 5
    data = open(ram, "rb").read()
    B = lambda i, a: data[(i - 1) * RAM + a]
    S = lambda i: (lambda v: v - 256 if v > 127 else v)(B(i, P_SPD))
    rows = []
    for tag, name, label, ranges in ROUTE:
        allrows = [i for f, l in ranges for i in range(f, l + 1)]
        ctrl = [i for i in allrows if B(i, GES) == 8 and B(i, P_YHI) == 1]
        if not ctrl:
            continue
        # a sub-area's player-control start (slack_table's definition: GES 8 with OperMode_Task 3)
        starts = []
        for f, l in ranges:
            c = [i for i in range(f, l + 1) if B(i, GES) == 8 and B(i, TASK) == 3 and B(i, P_YHI) == 1]
            if c:
                starts.append(c[0])
        off = [i for i in ctrl if abs(S(i)) not in (40, 24)]
        runs, s, prev = [], None, None
        for i in off:
            if s is None:
                s = i
            elif i - prev > gap:
                runs.append((s, prev))
                s = i
            prev = i
        if s is not None:
            runs.append((s, prev))
        for a, b in runs:
            xs = [B(i, P_PAGE) * 256 + B(i, P_X) for i in range(a, b + 1)]
            dx = max(xs) - min(xs)
            frames = b - a + 1
            loss = frames - dx / 2.5
            start = any(0 <= a - s0 <= 2 for s0 in starts)
            if loss < minloss:
                continue
            rows.append((loss, tag, a, b, frames, min(xs), max(xs), dx, start,
                         min(B(i, P_Y) for i in range(a, b + 1)),
                         max(B(i, P_Y) for i in range(a, b + 1))))
    rows.sort(reverse=True)
    print(f"{'loss':>6} {'area':6s} {'rows':>13} {'f':>4} {'x':>13} {'dx':>5} {'y band':>9}  note")
    tot = 0
    for loss, tag, a, b, frames, x0, x1, dx, start, y0, y1 in rows:
        tot += loss
        note = "LEVEL-START RAMP (forced, F225)" if start else \
               f"geometry: cols {x0//16}-{x1//16}"
        print(f"{loss:6.0f} {tag:6s} {a:6d}-{b:<6d} {frames:4d} {x0:6d}-{x1:<6d} {dx:5d} {y0:4d}-{y1:<4d}  {note}")
    geo = sum(r[0] for r in rows if not r[8])
    print(f"\ntotal priced loss {tot:.0f} frames; of that {tot-geo:.0f} in forced level-start ramps "
          f"and {geo:.0f} in geometry")

if __name__ == "__main__":
    main()
