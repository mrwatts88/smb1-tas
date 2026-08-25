#!/usr/bin/env python3
"""H50/F254 — price a SECOND StarFlagObject at every flag level, by poking rather than exploiting.

`RunStarFlagObj` is dispatched per enemy slot but drives global state, except `EnemyIntervalTimer`,
which is per slot: with two `$31` objects the second one reads its never-written timer as 0 and
`DelayToAreaEnd` advances to task 5 in the same frame, so F27's (v+1)+105 framerule wait collapses.
This measures the consequence directly on QuickNES: poke `Enemy_ID[slot] = $31` and its `Enemy_Flag`
into a free slot a few frames before the flagpole, and compare the frame `StarFlagTaskControl` ($0746)
first reaches 5 (the area change, F27 — the quantity a flag level is measured in) against the control.

Usage: tools/starflag_probe.py [--frames N]
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
EID, EFLAG, SFTC = 0x16, 0x0f, 0x746
NF = 18100

def run(pokes, tag):
    cmd = ["./build/harness", CORE, ROM, WR, "--frames", str(NF), "--input-skip", "2",
           "--ram", f"{SP}/sfp_{tag}.ram", "--quiet"]
    for p in pokes:
        cmd += ["--poke", p]
    subprocess.run(cmd, check=True, capture_output=True)
    return np.memmap(f"{SP}/sfp_{tag}.ram", dtype=np.uint8, mode="r").reshape(-1, 2048)

def main():
    base = run([], "ctl")
    sf = base[:, SFTC].astype(int)
    # each flag level's area change = a rising edge to 5 in StarFlagTaskControl
    ends = [f for f in range(1, len(sf)) if sf[f] == 5 and sf[f - 1] != 5]
    print(f"control: StarFlagTaskControl reaches 5 at core frames {ends}")
    names = ["1-1", "4-1", "8-1", "8-2", "8-3"]
    total = 0
    print(f"\n{'level':>5} {'control':>8} {'2 flags':>8} {'gain':>6}  {'poke':>28}")
    for i, e in enumerate(ends[:5]):
        # the grab is where SFTC first becomes non-zero for this level
        g = next(f for f in range(e, 0, -1) if sf[f] == 0) + 1
        pf = g - 6
        ids = [int(base[pf, EID + k]) for k in range(6)]
        free = next((k for k in range(6) if ids[k] == 0 and int(base[pf, EFLAG + k]) == 0), None)
        if free is None:
            print(f"{names[i]:>5} {e:8d}  no free enemy slot at core {pf}: {[hex(x) for x in ids]}")
            continue
        pk = [f"0x{EID+free:x}=0x31@{pf}", f"0x{EFLAG+free:x}=0x01@{pf}"]
        r = run(pk, names[i])
        s2 = r[:, SFTC].astype(int)
        e2 = next((f for f in range(g, len(s2)) if s2[f] == 5), None)
        gain = e - e2 if e2 else None
        if gain:
            total += gain
        print(f"{names[i]:>5} {e:8d} {str(e2):>8} {str(gain):>6}  slot {free} @core {pf}")
    print(f"\nTOTAL measured gain over the five flag levels: {total} frames "
          f"(target needs 21; the WR is 17,868)")
    print("NOTE: this is the CONSEQUENCE priced, not an exploit. No injector for a second $31 is "
          "known — F252 closed the player head-bump write, F253 shows the enemy writer only ever "
          "stores $00, and CastleObject's `lda CurrentPageLoc / beq ExitCastle` suppresses the "
          "page-0 castles that 4-1/8-1/8-2/8-3 carry.")

if __name__ == "__main__":
    main()
