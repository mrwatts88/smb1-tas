#!/usr/bin/env python3
"""Where in the whole movie is Mario NOT at the relevant speed cap?

Running cap is 40 (B held), walking 24, swimming 24.  A frame at the cap is a frame no search can
improve by moving better; the frames that can move are the ones off it.  Prints, per level and per
area-run, the control frames and how many are off cap, plus the biggest contiguous off-cap runs.
"""
import numpy as np, sys
r = np.memmap("data/wr/fceux_wr.ram", dtype=np.uint8, mode="r").reshape(-1, 2048)
LEV = [("1-1",42,1944),("1-2",1944,3766),("4-1",3766,6042),("4-2",6042,7723),
       ("8-1",7723,10813),("8-2",10813,12956),("8-3",12956,15057),("8-4",15057,17875)]
print(f"{'lvl':>4} {'rows':>13} {'tot':>5} {'ctrl':>5} {'@40':>5} {'@24':>5} {'off':>5} {'off%':>5}  biggest off-cap runs (row:len)")
for name, lo, hi in LEV:
    q = r[lo:hi]
    ges = q[:, 0x0e].astype(int)
    sp = q[:, 0x57].astype(int); sp = np.where(sp > 127, sp - 256, sp)
    ctrl = ges == 8
    a = np.abs(sp)
    off = ctrl & (a != 40) & (a != 24)
    # contiguous runs of off
    runs, s = [], None
    for i in range(len(off)):
        if off[i] and s is None: s = i
        elif not off[i] and s is not None:
            runs.append((lo + s, i - s)); s = None
    if s is not None: runs.append((lo + s, len(off) - s))
    runs.sort(key=lambda t: -t[1])
    top = " ".join(f"{p}:{n}" for p, n in runs[:6])
    print(f"{name:>4} {lo:6d}-{hi:<6d} {hi-lo:5d} {ctrl.sum():5d} {(ctrl&(a==40)).sum():5d} "
          f"{(ctrl&(a==24)).sum():5d} {off.sum():5d} {100*off.sum()/max(1,ctrl.sum()):4.0f}%  {top}")
