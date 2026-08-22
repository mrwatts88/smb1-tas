#!/usr/bin/env python3
"""Reconstruct a level's block map (metatiles, 13 rows x N columns) from a full-RAM dump of a playthrough.

The game keeps only two pages of metatiles in RAM (Block_Buffer_1 $0500 for even pages, Block_Buffer_2 $05D0 for
odd pages; byte = row*16 + column), written by the area parser 1-2 screens ahead of the player. Absolute column
c is valid in its buffer from the moment the renderer (CurrentPageLoc*16 + CurrentColumnPos) has passed it until
it reaches c + 32. We read each column the first time it is valid on a frame with no parser task in progress
(AreaParserTaskNum == 0) — the pristine level before the player changes any block — and report any later change.

Usage: tools/blockmap_from_dump.py RAMFILE FIRST LAST [--ascii] [--rust NAME] [--compare FILE NAME]
  FIRST..LAST  dump rows of one area (from its load to its exit); FIRST may be the load row
  --ascii      print the map (one char per block: '.' empty, '#' solid $10-$3F, 'c' coin, 'o' other)
  --rust NAME  print a `blockbuf!(NAME, WIDTH, [[...]])` array in MrWint/smb-opt's format
  --compare FILE NAME  compare with the blockbuf! array NAME in FILE (e.g. third_party/smb-opt/src/blockbuffer/world1.rs BB11)
Output format of --rust is that of third_party/smb-opt/src/blockbuffer/world1.rs (rows 0..12 top to bottom).
"""
import re
import sys

sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
from ram_trace import load_symbols  # noqa: E402

SYMS = load_symbols()

def reconstruct(data, first, last, verbose=True):
    A = lambda n: SYMS[n]
    ram = lambda row, a: data[(row - 1) * 2048 + a]
    cols = {}      # absolute column -> [13 bytes]
    changes = {}   # absolute column -> list of (row, [13 bytes]) later readings that differ
    started = False
    render_start = None  # first column rendered after the load = entrance page * 16 (InitializeArea)
    for row in range(first, last + 1):
        # the renderer/buffers belong to the new area only once it runs (GameEngineSubroutine 8 = control);
        # by then the first 1.5 screens are rendered and still in the buffers
        if not started:
            ges = ram(row, A('GameEngineSubroutine'))
            if ges == 0 and render_start is None:
                render_start = ram(row, A('CurrentPageLoc')) * 16
            if ges != 8:
                continue
            started = True
            if render_start is None:
                print("warning: range does not include the area load; assuming the renderer started at column 0", file=sys.stderr)
                render_start = 0
        if ram(row, A('AreaParserTaskNum')) != 0:
            continue
        R = ram(row, A('CurrentPageLoc')) * 16 + ram(row, A('CurrentColumnPos'))
        for c in range(max(render_start, R - 32), R):
            base = 0x500 + (0xd0 if (c >> 4) & 1 else 0) + (c & 15)
            vals = [ram(row, base + k * 16) for k in range(13)]
            if c not in cols:
                cols[c] = vals
            elif vals != cols[c]:
                lst = changes.setdefault(c, [])
                if not lst or lst[-1][1] != vals:
                    lst.append((row, vals))
    if verbose:
        print(f"columns {min(cols)}..{max(cols)} ({len(cols)} read); {len(changes)} columns changed later", file=sys.stderr)
        for c in sorted(changes)[:20]:
            for row, vals in changes[c][:2]:
                diff = [(k, cols[c][k], vals[k]) for k in range(13) if vals[k] != cols[c][k]]
                print(f"  column {c} (page {c >> 4} col {c & 15}) changed at row {row}: {diff}", file=sys.stderr)
    return cols

def as_grid(cols):
    width = max(cols) + 1
    grid = [[0] * width for _ in range(13)]
    for c, vals in cols.items():
        for k in range(13):
            grid[k][c] = vals[k]
    return grid

def ascii_map(grid):
    out = []
    for k in range(13):
        line = ''
        for v in grid[k]:
            line += '.' if v == 0 else '#' if 0x10 <= v < 0x40 else 'c' if v in (0xc2, 0xc3) else 'o'
        out.append(line)
    return '\n'.join(out)

def rust_array(name, grid):
    width = len(grid[0])
    rows = []
    for k in range(13):
        rows.append('[' + ','.join(f'{v:#04x}' if v else '0' for v in grid[k]) + ']')
    return f"blockbuf!({name}, {width}, [\n" + ',\n'.join(rows) + "\n]);"

def parse_rust(path, name):
    s = open(path).read()
    m = re.search(r'blockbuf!\(\s*' + re.escape(name) + r'\s*,\s*([^,]+),\s*\[(.*?)\]\s*\)\s*;', s, re.S)
    if not m:
        raise SystemExit(f"{name} not found in {path}")
    width = eval(m.group(1))
    body = m.group(2)
    rows = re.findall(r'\[([^\[\]]*)\]', body)
    grid = []
    for r in rows:
        vals = [int(t.strip(), 0) for t in r.split(',') if t.strip()]
        assert len(vals) == width, (len(vals), width)
        grid.append(vals)
    assert len(grid) == 13
    return grid

def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    ramfile, first, last = args[0], int(args[1]), int(args[2])
    data = open(ramfile, 'rb').read()
    cols = reconstruct(data, first, last)
    grid = as_grid(cols)
    if '--ascii' in sys.argv:
        print(ascii_map(grid))
    if '--rust' in sys.argv:
        name = sys.argv[sys.argv.index('--rust') + 1]
        print(rust_array(name, grid))
    if '--compare' in sys.argv:
        i = sys.argv.index('--compare')
        ref = parse_rust(sys.argv[i + 1], sys.argv[i + 2])
        width = min(len(ref[0]), len(grid[0]))
        read = sorted(c for c in cols if c < width)
        diffs = [(k, c, grid[k][c], ref[k][c]) for k in range(13) for c in read if grid[k][c] != ref[k][c]]
        print(f"compare: our width {len(grid[0])}, ref width {len(ref[0])}, {len(diffs)} differing cells over the {len(read)} read columns {read[0]}..{read[-1]}")
        for d in diffs[:30]:
            print(f"  row {d[0]} col {d[1]} (page {d[1] >> 4} col {d[1] & 15}): dump {d[2]:#04x} ref {d[3]:#04x}")

if __name__ == '__main__':
    main()
