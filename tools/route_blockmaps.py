#!/usr/bin/env python3
"""Build a block map (13 rows x N columns of metatiles) for every area on the WR's route.

Wraps tools/blockmap_from_dump.py: runs its column reconstruction over each dump range in which
an area is live, merges repeated visits to the same area (1-1 is entered twice, either side of
the bonus room), and writes data/blockmaps/<tag>.txt (ascii) + <tag>.grid (one hex byte per
cell, 13 lines) + <tag>.log (the reconstruction's stderr notes).

Ranges come from tools/slack_table.py's area-load table over data/wr/fceux_wr.ram (F26/F28).

Usage: tools/route_blockmaps.py [RAMFILE] [--only TAG]
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blockmap_from_dump as B  # noqa: E402

OUT = "data/blockmaps"

# tag, human name, disassembly area label, [(first_row, last_row), ...]
ROUTE = [
    ("w11",    "1-1 main",              "L_GroundArea6",       [(43, 612), (927, 1944)]),
    ("w11b",   "1-1 bonus room",        "L_UndergroundArea3",  [(613, 926)]),
    ("w12i",   "1-2 pipe intro",        "L_UndergroundArea4?", [(1945, 2443)]),
    ("w12",    "1-2 main",              "L_UndergroundArea1",  [(2444, 3814)]),
    ("w41",    "4-1",                   "L_GroundArea17",      [(3815, 6042)]),
    ("w42i",   "4-2 pipe intro",        "L_UndergroundArea4?", [(6043, 6541)]),
    ("w42m",   "4-2 main",              "L_UndergroundArea2",  [(6542, 7220)]),
    ("w42w",   "4-2 warp zone ($2F)",   "L_GroundArea16",      [(7221, 7771)]),
    ("w81",    "8-1",                   "L_GroundArea19",      [(7772, 10813)]),
    ("w82",    "8-2",                   "L_GroundArea3",       [(10814, 12956)]),
    ("w83",    "8-3",                   "L_GroundArea?",       [(12957, 15057)]),
    ("w84r1",  "8-4 room 1",            "L_CastleArea6",       [(15058, 15795)]),
    ("w84r2",  "8-4 room 2 (water)",    "L_WaterArea3",        [(15796, 16232)]),
    ("w84r3",  "8-4 room 3",            "L_CastleArea?",       [(16233, 16597)]),
    ("w84r4",  "8-4 room 4",            "L_CastleArea?",       [(16598, 17467)]),
    ("w84r5",  "8-4 room 5 (Bowser)",   "L_CastleArea?",       [(17468, 17868)]),
]

def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    ram = args[0] if args else "data/wr/fceux_wr.ram"
    only = sys.argv[sys.argv.index("--only") + 1] if "--only" in sys.argv else None
    data = open(ram, "rb").read()
    os.makedirs(OUT, exist_ok=True)
    for tag, name, label, ranges in ROUTE:
        if only and tag != only:
            continue
        notes = []
        cols = {}
        for first, last in ranges:
            saved, sys.stderr = sys.stderr, open(os.devnull, "w")
            try:
                part = B.reconstruct(data, first, last, verbose=False)
            finally:
                sys.stderr.close()
                sys.stderr = saved
            if not part:
                notes.append(f"rows {first}..{last}: no columns read (no GES==8 frame in range)")
                continue
            notes.append(f"rows {first}..{last}: columns {min(part)}..{max(part)} ({len(part)} read)")
            for c, v in part.items():
                if c in cols and cols[c] != v:
                    notes.append(f"  merge conflict at column {c}: {cols[c]} vs {v} (kept first)")
                cols.setdefault(c, v)
        if not cols:
            print(f"{tag:6s} {name:22s} SKIPPED - no columns readable ({'; '.join(notes)})")
            continue
        grid = B.as_grid(cols)
        with open(f"{OUT}/{tag}.txt", "w") as f:
            f.write(f"# {tag}  {name}  {label}\n")
            f.write(f"# columns {min(cols)}..{max(cols)} ({len(cols)} read) from {ram} {ranges}\n")
            f.write(B.ascii_map(grid) + "\n")
        with open(f"{OUT}/{tag}.grid", "w") as f:
            for k in range(13):
                f.write(" ".join(f"{v:02x}" for v in grid[k]) + "\n")
        with open(f"{OUT}/{tag}.log", "w") as f:
            f.write(f"{tag}  {name}  {label}\n" + "\n".join(notes) + "\n")
        missing = sorted(set(range(min(cols), max(cols) + 1)) - set(cols))
        print(f"{tag:6s} {name:22s} cols {min(cols):3d}..{max(cols):3d} "
              f"({len(cols)} read, {len(missing)} gaps)")

if __name__ == "__main__":
    main()
