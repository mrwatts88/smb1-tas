#!/usr/bin/env python3
"""Splice a NES-order input segment (one byte per frame, as written by `smb-opt bfscx-path --out` /
tools/chain_inputs.py) into an .fm2 movie, replacing frames [START, START+len(SEG)) and truncating the
movie after the segment plus PAD blank frames. Header lines are kept verbatim (power-on command lines
in the untouched prefix included). P2.3c-2c: builds the 4-2 `553` verification movie from the WR fm2.

usage: tools/splice_fm2.py WR.fm2 SEG.bin START OUT.fm2 [--or-last HEX] [--pad N]
  --or-last HEX   OR this byte into the segment's final frame (e.g. 0x20 = Down for a pipe entry, F74)
  --pad N         blank input frames appended after the segment (default 400)
"""
import sys

BTN = "RLDUTSBA"
BIT = {"R": 0x80, "L": 0x40, "D": 0x20, "U": 0x10, "T": 0x08, "S": 0x04, "B": 0x02, "A": 0x01}

def render(v):
    return "".join(c if v & BIT[c] else "." for c in BTN)

def main():
    a = sys.argv[1:]
    src, segp, start, dst = a[0], a[1], int(a[2]), a[3]
    orlast = 0; pad = 400; i = 4
    while i < len(a):
        if a[i] == "--or-last": orlast = int(a[i + 1], 16); i += 2
        elif a[i] == "--pad": pad = int(a[i + 1]); i += 2
        else: raise SystemExit(f"unknown option {a[i]}")
    seg = bytearray(open(segp, "rb").read())
    if orlast: seg[-1] |= orlast
    header, inputs = [], []
    for line in open(src, encoding="utf-8", errors="replace"):
        (inputs if line.startswith("|") else header).append(line.rstrip("\n"))
    assert start + len(seg) <= len(inputs), "segment runs past the movie"
    out = inputs[:start] + [f"|0|{render(v)}|........||" for v in seg] + ["|0|........|........||"] * pad
    with open(dst, "w") as f:
        for line in header: f.write(line + "\n")
        for line in out: f.write(line + "\n")
    print(f"{dst}: {len(out)} input frames = {start} kept + {len(seg)} spliced (last byte {seg[-1]:#04x}) + {pad} pad")

if __name__ == "__main__":
    main()
