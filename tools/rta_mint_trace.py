#!/usr/bin/env python3
"""RTA-1: per-frame scroll-offset trace of a QuickNES RAM dump (build/harness --ram), for reading
the 4-2 wrong-warp "mint" (scroll offset = Player x - ScreenLeft; the warp needs >= 132 at pipe
entry with Player_X_Scroll = 0, F120/F129).

usage: tools/rta_mint_trace.py RAMFILE FIRST LAST [--every N] [--rows]
  default: one line every N rows (5) plus every row where the offset changes, an impede happens
           (SideCollisionTimer set to 16) or GameEngineSubroutine changes.
  --rows : every row, with the joypad byte decoded and the x subpixel (for reading a mint's inputs).
Rows are 1-based = state after that frame; with `--input-skip 2 --reset0` the pad shown on row r is
fm2 record r+1 (checked against data/wr/maru-rtarules.fm2, docs/experiments/RTA-1-maru-42-mint.md).
Joypad bits are the game's ($06FC): A=$80 B=$40 Sel=$20 St=$10 U=$08 D=$04 L=$02 R=$01."""
import sys

A = dict(GES=0x0e, state=0x1d, facing=0x33, xspd=0x57, ppage=0x6d, px=0x86, yspd=0x9f, py=0xce,
         slp=0x071a, slx=0x071c, xscroll=0x06ff, sct=0x0785, aptr=0x0750, epage=0x0751, pad=0x06fc,
         xsub=0x0705)

def s8(v): return v - 256 if v > 127 else v

def pad(v):
    names = ["R", "L", "D", "U", "St", "Se", "B", "A"]
    return "+".join(n for i, n in enumerate(names) if v & (1 << i)) or "-"

def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    ram = open(args[0], "rb").read()
    first, last = int(args[1]), int(args[2])
    every = int(sys.argv[sys.argv.index("--every") + 1]) if "--every" in sys.argv else 5
    rows = "--rows" in sys.argv

    def row(r):
        b = ram[(r - 1) * 2048:r * 2048]
        d = {k: b[a] for k, a in A.items()}
        d["x"] = d["ppage"] * 256 + d["px"]
        d["sl"] = d["slp"] * 256 + d["slx"]
        d["off"] = d["x"] - d["sl"]
        d["xs"] = s8(d["xspd"])
        return d

    if rows:
        print("row   pad        x  sub  xs   y  ys st face sct    SL off")
    prev = None
    for r in range(first, last + 1):
        d = row(r)
        if rows:
            print(f"{r:5d} {pad(d['pad']):8s} {d['x']:5d} {d['xsub']:3d} {d['xs']:3d} {d['py']:3d} "
                  f"{s8(d['yspd']):3d} {d['state']:2d} {d['facing']:4d} {d['sct']:3d} {d['sl']:5d} {d['off']:3d}")
            continue
        tag = ""
        if prev is not None:
            if d["off"] != prev["off"]: tag = f"<< off {prev['off']}->{d['off']}"
            if d["sct"] > prev["sct"]: tag += " [impede]"
            if d["GES"] != prev["GES"]: tag += f" GES {prev['GES']}->{d['GES']}"
        if tag or (r - first) % every == 0:
            print(f"{r:5d} x={d['x']:5d} y={d['py']:3d} xs={d['xs']:3d} st={d['state']} face={d['facing']} "
                  f"SL={d['sl']:5d} off={d['off']:3d} sct={d['sct']:2d} xscr={d['xscroll']} GES={d['GES']} "
                  f"aptr={d['aptr']:02x} ep={d['epage']} {tag}")
        prev = d

if __name__ == "__main__":
    main()
