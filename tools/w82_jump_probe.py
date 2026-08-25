#!/usr/bin/env python3
"""H48 probe — can Mario jump 8-2's col-206/207 wall straight off the col-203 pillar?

Splices a jump into the WR's own inputs at the pillar and replays on the QuickNES core.  For each
(jump frame, A-hold length) it reports whether the right side probe survives the wall's column
window x in [3283, 3314] (which needs Player_Y_Position <= 55 throughout, F245), the max x reached,
and the core frame StarFlagTaskControl ($0746) first hits 5 (the quantity 8-2 is measured in --
F230/F237; WR = 12952, a record needs <= 12931).

Usage: tools/w82_jump_probe.py [--out DIR] [--jstart A,B] [--holds ...] [--pre BYTE] [--btn HEX]
"""
import os
import subprocess
import sys

import numpy as np

SP = os.environ.get("SCRATCH", "/tmp/claude-1000/-home-mattwatts-Documents-smb1-tas/"
                               "e3753b99-69a6-49ff-a185-c6955fe32bea/scratchpad")
CORE = "third_party/QuickNES_Core/quicknes_libretro.so"
ROM = "roms/Super Mario Bros. (W) [!].nes"
WR = "data/wr/wr_inputs.bin"
R, L, D, U, B, A = 0x80, 0x40, 0x20, 0x10, 0x02, 0x01
NFRAMES = 13000
WALL_LO, WALL_HI = 3283, 3314      # right side probe inside cols 206-207
Y_CLEAR = 55                        # side row <= 2 <=> Player_Y_Position <= 55

def run(inputs, tag):
    p = os.path.join(SP, f"probe_{tag}.bin")
    open(p, "wb").write(inputs)
    subprocess.run(["./build/harness", CORE, ROM, p, "--frames", str(NFRAMES),
                    "--input-skip", "2", "--ram", os.path.join(SP, f"probe_{tag}.ram")],
                   check=True, capture_output=True)
    return np.memmap(os.path.join(SP, f"probe_{tag}.ram"), dtype=np.uint8, mode="r").reshape(-1, 2048)

def main():
    wr = bytearray(open(WR, "rb").read())
    jstarts = range(*[int(v) for v in (sys.argv[sys.argv.index("--jstart") + 1].split(","))]) \
        if "--jstart" in sys.argv else range(12280, 12290)
    holds = [int(v) for v in sys.argv[sys.argv.index("--holds") + 1].split(",")] \
        if "--holds" in sys.argv else [6, 10, 14, 18, 22, 26, 30, 34]
    air = int(sys.argv[sys.argv.index("--btn") + 1], 16) if "--btn" in sys.argv else (R | B)
    print(f"H48 probe: jump spliced into {WR} at the 8-2 pillar; air buttons {air:#04x}; "
          f"wall window x[{WALL_LO},{WALL_HI}] needs Y <= {Y_CLEAR}")
    print(f"{'jf':>6} {'hold':>4} {'maxx':>6} {'Y@3283':>7} {'minY-in':>8} {'minspd-in':>9} "
          f"{'cleared':>8} {'flag5':>6}  note")
    best = None
    for jf in jstarts:
        for h in holds:
            inp = bytes(wr[:jf + 2]) + bytes([air | A] * h) + bytes([air] * (NFRAMES - jf - h))
            r = run(inp, "s")
            x = r[:, 0x6d].astype(int) * 256 + r[:, 0x86].astype(int)
            y = r[:, 0xce].astype(int)
            sp = r[:, 0x57].astype(int)
            sp = np.where(sp > 127, sp - 256, sp)
            w = [f for f in range(jf, min(jf + 200, NFRAMES)) if WALL_LO <= x[f] <= WALL_HI]
            first = [f for f in range(jf, min(jf + 200, NFRAMES)) if x[f] >= WALL_LO]
            y0 = y[first[0]] if first else -1
            miny = min((y[f] for f in w), default=-1)
            minsp = min((sp[f] for f in w), default=-1)
            cleared = bool(w) and max(y[f] for f in w) <= Y_CLEAR
            fl = [f for f in np.nonzero(r[:, 0x746] == 5)[0] if f > jf]
            flag = int(fl[0]) if fl else -1
            mx = int(x[jf:jf + 200].max())
            note = ""
            if cleared:
                note = "CLEARS THE WALL"
                if best is None or (flag != -1 and flag < best[0]):
                    best = (flag, jf, h)
            print(f"{jf:6d} {h:4d} {mx:6d} {y0:7d} {miny:8d} {minsp:9d} {str(cleared):>8} "
                  f"{flag:6d}  {note}" + (f" [{12952-flag:+d} vs WR]" if flag != -1 else ""))
    if best:
        print(f"\nbest clearing run: flag5 at core {best[0]} (WR 12952, record <= 12931) "
              f"from jump frame {best[1]} hold {best[2]}")
    else:
        print("\nno (jump frame, hold) in this sweep clears the wall")

if __name__ == "__main__":
    main()
