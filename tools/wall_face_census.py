#!/usr/bin/env python3
"""E9a - the wall-face census (H46), static half.

Enumerates every wall face on the WR's route and classifies whether SMB1's side-collision
routine admits Mario through it at speed.

THE MECHANIC, read out of data/disasm/smbdis.asm (DoPlayerSideCheck 12022-12060,
CheckSideMTiles 12063-12078, ImpedePlayerMove 12318-12351, BlockBufferCollision 13053-13090):

  ChkCollSize picks the block-buffer adder base $eb from BlockBufferAdderData = [$00,$07,$0e]:
  $00 big-on-land, $07 big-swimming, $0e small OR crouching.  The side check then probes
  $eb+3, $eb+4 (iteration 1, counter $00 = 2) and $eb+5, $eb+6 (iteration 2, counter $00 = 1).
  BlockBuffer_X_Adder/Y_Adder repeat in groups of 7, so the four side probes are

      big   ($eb=0):  (X+2, Y+8) (X+2, Y+24) | (X+13, Y+8) (X+13, Y+24)
      small ($eb=14): (X+2, Y+24) (X+2, Y+24) | (X+13, Y+24) (X+13, Y+24)

  i.e. iteration 1 is the LEFT side of the player and iteration 2 is the RIGHT side, and for
  small Mario each iteration probes ONE cell twice.  The loop EXITS at the first probe that
  finds something, and the counter it exits on is what ImpedePlayerMove sees:

      $00 = 2 (left probe hit)  -> RImpd -> `cpy #$01 / bpl ExIPM` -> moving RIGHT: NO IMPEDE
      $00 = 1 (right probe hit) ->         `cpy #$00 / bmi ExIPM` -> moving RIGHT: speed := 0

  So: while the LEFT probe is in a non-empty cell, a right-moving Mario is never impeded and
  the right probe is never consulted.  That is the walk-through primitive (F80/F239).

  Three metatile classes escape a collision entirely rather than reaching ImpedePlayerMove:
  hidden blocks $5f/$60 (ChkInvisibleMTiles -> ExCSM: no impede from EITHER side, and the cell
  is NOT consumed), coins $c2/$c3 (HandleCoinMetatile: no impede, cell erased to $00), and
  jumpsprings $67/$68 while JumpspringAnimCtrl != 0.  Climbable metatiles (>= $24/$6d/$8a/$c6
  by quadrant) reach HandleClimbing instead.  NOTE: "solid" in CheckForSolidMTiles ($10/$61/
  $88/$c4) is a HEAD-BUMP classifier, not a collision classifier - a brick is not "solid" there
  but it does block the side check.  Blocking == non-empty, minus the escapes above.

  A wall face at column `a` of a blocking run therefore admits a full-speed walk-through iff
  the cell at (row, a-1) is non-empty AND PERSISTENT, because the left probe sits in column
  a-1 for the whole 11 px between "right probe enters column a" (x = 16a-13) and "left probe
  enters column a" (x = 16a-2).  Only $5f/$60 qualify: they are non-empty, never impede, and
  are not consumed by a side touch.  A coin does not: the right probe enters column a-1
  eleven pixels before the left probe does and collects it, so the cell is $00 by the time it
  would matter (this is why 4-2's coin at (29,10) needed F93's 31-frame foot drift).

Usage: tools/wall_face_census.py [--ram data/wr/fceux_wr.ram] [--only TAG] [--md FILE]
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from route_blockmaps import ROUTE  # noqa: E402

MAPS = "data/blockmaps"
RAM = 0x800
P_X, P_PAGE, P_Y, P_SPD, P_STATE, P_YHI = 0x86, 0x6d, 0xce, 0x57, 0x1d, 0xb5
P_SIZE, P_CROUCH, P_SWIM, GES = 0x0754, 0x0714, 0x0704, 0x0e

SOLID_T = [0x10, 0x61, 0x88, 0xc4]     # CheckForSolidMTiles (head-bump classifier)
CLIMB_T = [0x24, 0x6d, 0x8a, 0xc6]     # CheckForClimbMTiles
HIDDEN, COIN, SPRING, PIPETOP, SIDEPIPE = {0x5f, 0x60}, {0xc2, 0xc3}, {0x67, 0x68}, {0x1c, 0x6b}, {0x6c, 0x1f}

# adder groups (BlockBuffer_X_Adder / _Y_Adder, 7 per group)
XA = [0x08, 0x03, 0x0c, 0x02, 0x02, 0x0d, 0x0d]
YA_BIG = [0x04, 0x20, 0x20, 0x08, 0x18, 0x08, 0x18]
YA_SMALL = [0x12, 0x20, 0x20, 0x18, 0x18, 0x18, 0x18]

def head_solid(m):
    return m >= SOLID_T[(m >> 6) & 3]

def climbable(m):
    return m >= CLIMB_T[(m >> 6) & 3]

def cls(m):
    if m == 0:
        return "EMPTY"
    if m in HIDDEN:
        return "HIDDEN"
    if m in COIN:
        return "COIN"
    if climbable(m):
        return "CLIMB"
    if m in SPRING:
        return "SPRING"
    if m in SIDEPIPE:
        return "SIDEPIPE"
    return "BLOCK"

def blocking(m):
    """True iff a right probe in this cell reaches ImpedePlayerMove with $00 = 1."""
    return cls(m) in ("BLOCK", "SIDEPIPE", "SPRING")

def load_grid(tag):
    path = f"{MAPS}/{tag}.grid"
    if not os.path.exists(path):
        return None
    return [[int(t, 16) for t in line.split()] for line in open(path)]

def side_row(y, small=True):
    """Block-buffer row index of the side probe for a player at Player_Y_Position y."""
    ya = (YA_SMALL if small else YA_BIG)[3]      # $18 small / $08 big-upper
    return ((y + ya) & 0xF0) // 16 - 2

def probe_rows(y, small=True):
    ya = YA_SMALL if small else YA_BIG
    rows = sorted({(((y + ya[i]) & 0xF0) // 16 - 2) for i in (3, 4)})
    return rows

def route_occupancy(data, ranges):
    """Per-frame probe geometry over the WR dump for one area: which (row, column) cells the
    left probe visited, and the y band the player occupied over each column."""
    occ = set()
    band = {}          # absolute column of x+2 -> (min side row, max side row)
    xrange = [None, None]
    for first, last in ranges:
        for row in range(first, last + 1):
            base = (row - 1) * RAM
            if data[base + P_YHI] != 1:
                continue
            g = data[base + GES]
            if g not in (7, 8):          # player entrance / player control
                continue
            x = data[base + P_X]
            page = data[base + P_PAGE]
            y = data[base + P_Y]
            small = data[base + P_SIZE] != 0 or data[base + P_CROUCH] != 0
            ax = page * 256 + x
            xrange[0] = ax if xrange[0] is None else min(xrange[0], ax)
            xrange[1] = ax if xrange[1] is None else max(xrange[1], ax)
            for r in probe_rows(y, small):
                c = (ax + 2) >> 4
                occ.add((r, c))
                lo, hi = band.get(c, (99, -1))
                band[c] = (min(lo, r), max(hi, r))
    return occ, band, xrange

def runs_in_row(grid, r):
    row = grid[r]
    out, c = [], 0
    n = len(row)
    while c < n:
        if blocking(row[c]):
            a = c
            while c < n and blocking(row[c]):
                c += 1
            out.append((a, c - 1))
        else:
            c += 1
    return out

def census(tag, name, grid, occ, band, xrange):
    faces = []
    n = len(grid[0])
    for r in range(13):
        for a, b in runs_in_row(grid, r):
            if a == 0:
                continue                       # level edge / off-map
            left = grid[r][a - 1]
            lc = cls(left)
            if lc == "HIDDEN":
                verdict = "ADMITS-STATIC"
            elif lc == "COIN":
                verdict = "COIN-DEAD"          # collected by the right probe 11 px earlier
            elif lc == "CLIMB":
                verdict = "CLIMB"
            else:
                verdict = "REFUSES"
            # entry from above: a column inside the run whose row below does not block the feet
            drop = [c for c in range(a, b + 1) if r + 1 > 12 or not blocking(grid[r + 1][c])]
            # clearance above the face (how many empty rows sit over column a)
            clear = 0
            rr = r - 1
            while rr >= 0 and not blocking(grid[rr][a]):
                clear += 1
                rr -= 1
            wr_row_here = band.get(a - 1) or band.get(a)
            on_route = (r, a - 1) in occ or (r, a) in occ
            faces.append(dict(tag=tag, row=r, a=a, b=b, left=left, lclass=lc, verdict=verdict,
                              width=b - a + 1, drop=drop, clear=clear,
                              floor=all(blocking(grid[r + 1][c]) for c in range(a, b + 1)) if r < 12 else True,
                              on_route=on_route, wr_band=wr_row_here,
                              in_x=(xrange[0] is not None and a * 16 <= xrange[1] + 32 and a * 16 >= xrange[0] - 32)))
    return faces

def main():
    ram = sys.argv[sys.argv.index("--ram") + 1] if "--ram" in sys.argv else "data/wr/fceux_wr.ram"
    only = sys.argv[sys.argv.index("--only") + 1] if "--only" in sys.argv else None
    data = open(ram, "rb").read()
    allf = []
    print(f"{'area':6s} {'faces':>6s} {'refuse':>7s} {'hidden':>7s} {'coin':>5s} {'climb':>6s} {'on-route':>9s}")
    for tag, name, label, ranges in ROUTE:
        if only and tag != only:
            continue
        grid = load_grid(tag)
        if grid is None:
            continue
        occ, band, xrange = route_occupancy(data, ranges)
        f = census(tag, name, grid, occ, band, xrange)
        allf += f
        c = lambda v: sum(1 for x in f if x["verdict"] == v)
        print(f"{tag:6s} {len(f):6d} {c('REFUSES'):7d} {c('ADMITS-STATIC'):7d} {c('COIN-DEAD'):5d} "
              f"{c('CLIMB'):6d} {sum(1 for x in f if x['on_route']):9d}")
    print()
    print("=== every face whose left neighbour is not empty ===")
    for x in allf:
        if x["lclass"] != "EMPTY":
            print(f"  {x['tag']:6s} row {x['row']:2d} cols {x['a']:3d}-{x['b']:3d} "
                  f"left={x['left']:#04x} ({x['lclass']}) -> {x['verdict']:14s} "
                  f"width {x['width']:2d} floor={int(x['floor'])} on_route={int(x['on_route'])}")
    print()
    print("=== hidden blocks ($5f/$60) on the route, with their neighbourhood ===")
    for tag, name, label, ranges in ROUTE:
        grid = load_grid(tag)
        if grid is None:
            continue
        occ, band, xrange = route_occupancy(data, ranges)
        for r in range(13):
            for c, m in enumerate(grid[r]):
                if m in HIDDEN:
                    rt = grid[r][c + 1] if c + 1 < len(grid[r]) else None
                    lf = grid[r][c - 1] if c else None
                    below = grid[r + 1][c] if r < 12 else None
                    print(f"  {tag:6s} row {r:2d} col {c:3d} (x {c*16}-{c*16+15}) value {m:#04x}  "
                          f"left={lf if lf is None else f'{lf:#04x}'} right={rt if rt is None else f'{rt:#04x}'} "
                          f"below={below if below is None else f'{below:#04x}'}  "
                          f"right-blocks={int(rt is not None and blocking(rt))} "
                          f"wr-side-rows-here={band.get(c)} on_route={int((r,c) in occ)}")

if __name__ == "__main__":
    main()

# ---------------------------------------------------------------------------------------------
# Big Mario ($eb = $00): the left probe covers TWO rows, (X+2, Y+8) upper and (X+2, Y+24) lower.
# Iteration 1 exits on the FIRST of them that is non-empty (the upper one defers to the lower on
# $1c/$6b/climbable), so a right-moving big Mario gets the free pass if EITHER left cell is
# non-empty.  A face at (r, a) therefore admits him two ways that small Mario does not have:
#   A) he stands one row LOWER  - probes (r-1, r), feet r+1 - free iff grid[r-1][a-1] != 0
#   B) he stands one row HIGHER - probes (r, r+1), feet r+2 - free iff grid[r+1][a-1] != 0
# (grid[r][a-1] is empty by construction: a is a blocking run's left end.)

def big_census(tag, grid, occ, band):
    out = []
    for r in range(13):
        for a, b in runs_in_row(grid, r):
            if a == 0:
                continue
            if cls(grid[r][a - 1]) != "EMPTY":
                continue                       # already caught by the small-Mario pass
            for label, pr, need in (("A: stand 1 row lower", r - 1, r + 1),
                                    ("B: stand 1 row higher", r + 1, r + 2)):
                if pr < 0 or pr > 12:
                    continue
                m = grid[pr][a - 1]
                if m == 0 or cls(m) == "CLIMB":
                    continue
                # can he be there?  case A needs a floor under his feet at row r+1 (or airborne)
                floor = (need <= 12 and blocking(grid[need][a - 1])) if need <= 12 else True
                out.append(dict(tag=tag, row=r, a=a, b=b, mode=label, probe_row=pr,
                                pass_tile=m, pass_cls=cls(m), feet_row=need,
                                feet_supported=floor, width=b - a + 1,
                                on_route=(r, a - 1) in occ or (pr, a - 1) in occ,
                                wr_band=band.get(a - 1)))
    return out
