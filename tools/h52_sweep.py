#!/usr/bin/env python3
"""H52 sweep: one-frame input substitutions in the 8-4 Bowser room before Bowser loads.

For each core frame t in [T0, T1] and each substitute pad, run
  ram_oracle --input-skip 2 --set-input t=PAD --ending-scan BASE
and collect Bowser's spawn frame, the best last input and the outcome counts.
Usage: tools/h52_sweep.py OUT.tsv [T0 T1 BASE JOBS]   (defaults 17590 17757 17820 10)
Reads: any best < 17846 is a record candidate; the spawn column shows which variants moved Bowser.
"""
import re, subprocess, sys
from concurrent.futures import ThreadPoolExecutor

CORE = "third_party/QuickNES_Core/quicknes_libretro.so"
ROM = "roms/Super Mario Bros. (W) [!].nes"
PADS = [0x80, 0x00, 0xC2]   # Right without B; no input; B+Right+Left
out = sys.argv[1]
t0, t1, base, jobs = (int(a) for a in (sys.argv[2:6] + ["17590", "17757", "17820", "10"][len(sys.argv[2:6]):]))

def one(args):
    t, pad = args
    cmd = ["./build/ram_oracle", CORE, ROM, "data/wr/wr_inputs.bin", "--input-skip", "2",
           "--ending-scan", str(base)]
    if t >= 0:
        cmd += ["--set-input", f"{t}={pad}"]
    r = subprocess.run(cmd, capture_output=True, text=True)
    o = r.stdout
    sp = re.search(r"bowser_spawn core=(-?\d+)", o)
    b = re.search(r"BEST last-input frame = (\d+)", o)
    oc = re.search(r"axe (\d+)\s+died (\d+)\s+pit (\d+)\s+timeout (\d+)", o)
    best = int(b.group(1)) if b else -1
    if best >= 1 << 30:
        best = -1
    return (t, pad, int(sp.group(1)) if sp else -2, best, *(oc.groups() if oc else ("?",) * 4))

tasks = [(-1, 0)] + [(t, p) for t in range(t0, t1 + 1) for p in PADS]
with open(out, "w") as f, ThreadPoolExecutor(jobs) as ex:
    f.write("t\tpad\tspawn\tbest\taxe\tdied\tpit\ttimeout\n")
    for row in ex.map(one, tasks):
        f.write("\t".join(str(x) for x in row) + "\n"); f.flush()
        if 0 < row[3] < 17846:
            print("*** RECORD CANDIDATE", row, flush=True)
print("done", out)
