#!/usr/bin/env python3
"""Convert an FCEUX .fm2 movie to a raw input stream: one byte per frame, port 1, NES bit order
A=$01 B=$02 Select=$04 Start=$08 Up=$10 Down=$20 Left=$40 Right=$80 (same as tools/lua padbyte()).
Prints the frame count and the frames carrying commands (bit 0 = soft reset, bit 1 = power).

Usage: tools/fm2_to_inputs.py MOVIE.fm2 OUT.bin
"""
import sys

BTN = "RLDUTSBA"  # fm2 field order; T = Start, S = Select
BIT = {"R": 0x80, "L": 0x40, "D": 0x20, "U": 0x10, "T": 0x08, "S": 0x04, "B": 0x02, "A": 0x01}

def main():
    src, dst = sys.argv[1], sys.argv[2]
    out, cmds = bytearray(), []
    for line in open(src, encoding="utf-8", errors="replace"):
        if not line.startswith("|"):
            continue
        f = line.rstrip("\n").split("|")
        cmd, p1 = int(f[1] or 0), f[2]
        if cmd:
            cmds.append((len(out), cmd))
        v = 0
        for ch, name in zip(p1, BTN):
            if ch != ".":
                v |= BIT[name]
        out.append(v)
    open(dst, "wb").write(out)
    print(f"{len(out)} frames -> {dst}; commands: {cmds}")

if __name__ == "__main__":
    main()
