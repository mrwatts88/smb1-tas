#!/usr/bin/env python3
"""E1 (Track E) — is level-entry state a pure function of the entry frame?

Reads the WR per-frame RAM dump and answers three questions:
  1. Does the LFSR (RandomBits $07a7-$07ae) advance exactly once per frame?  Where not, why?
  2. Do IntervalTimerControl ($077f) / FrameCounter ($0009) advance in lockstep with it?
  3. At each level entry, what is actually carried across the boundary (i.e. not cleared by
     InitializeArea, which clears $0000-$074b)?

Usage: tools/entry_state_scan.py [DUMP]
"""
import sys
import numpy as np

DUMP = sys.argv[1] if len(sys.argv) > 1 else "data/wr/fceux_wr.ram"
r = np.memmap(DUMP, dtype=np.uint8, mode="r").reshape(-1, 2048)
NF = r.shape[0]
print(f"dump: {DUMP}  frames={NF}")

RB = slice(0x7a7, 0x7af)          # RandomBits, 8 bytes
ITC = 0x77f
FC  = 0x009
OPER = 0x770
WORLD = 0x75f
LEVEL = 0x75c
AREA = 0x750

# --- 1. LFSR steps -----------------------------------------------------------------
rb = r[:, RB]
same = np.all(rb[1:] == rb[:-1], axis=1)
stall = np.nonzero(same)[0] + 1      # frame f where RandomBits(f) == RandomBits(f-1)
print(f"\n[1] LFSR stalls (RandomBits unchanged from previous frame): {len(stall)}")
print("    frames:", " ".join(str(x) for x in stall[:40]), "..." if len(stall) > 40 else "")

# --- 2. ITC / FrameCounter cadence ------------------------------------------------
itc = r[:, ITC].astype(int)
d_itc = (itc[:-1] - itc[1:]) % 256          # expect 1 each frame (wrap 0 -> 20 gives 236)
itc_stall = np.nonzero(d_itc == 0)[0] + 1
fc = r[:, FC].astype(int)
d_fc = (fc[1:] - fc[:-1]) % 256
fc_stall = np.nonzero(d_fc == 0)[0] + 1
print(f"\n[2] ITC stalls: {len(itc_stall)}   FrameCounter stalls: {len(fc_stall)}")
print("    ITC stall frames:", " ".join(str(x) for x in itc_stall[:40]))
print("    FC  stall frames:", " ".join(str(x) for x in fc_stall[:40]))
print(f"    LFSR stalls == ITC stalls? {np.array_equal(stall, itc_stall)}")
print(f"    LFSR stalls == FC stalls?  {np.array_equal(stall, fc_stall)}")

# --- 3. what is carried across a level boundary ------------------------------------
# level entries: rows where AreaPointer changes (a new area is loaded)
ap = r[:, AREA].astype(int)
loads = np.nonzero(ap[1:] != ap[:-1])[0] + 1
print(f"\n[3] AreaPointer changes at rows: {list(loads)}")

# InitializeArea clears $0000-$074b.  Everything above that survives unless rewritten.
# Find, just after each load, which cells in $074c-$07ff differ from a pure function of the
# frame index -- i.e. report their values so a human can see what is path-dependent.
NAMES = {0x74c:"GameEngineSubroutine?",0x74e:"AreaType",0x750:"AreaPointer",0x751:"EntrancePage",
         0x752:"AltEntranceControl",0x754:"HalfwayPage",0x757:"PrimaryHardMode",0x759:"GameTimerExpired",
         0x75a:"NumberofLives",0x75c:"LevelNumber",0x75e:"AreaNumber",0x75f:"WorldNumber",
         0x770:"OperMode",0x772:"OperMode_Task",0x774:"DisableScreenFlag",0x77f:"IntervalTimerControl",
         0x7a7:"RandomBits+0",0x7d7:"TopScore+0",0x7dd:"Score+0",0x7ed:"CoinTally0",0x7ee:"CoinTally1",
         0x7f8:"GameTimer0",0x7f9:"GameTimer1",0x7fa:"GameTimer2",0x7fc:"WorldSelect",0x7fd:"ContinueWorld",
         0x7ff:"WarmBootValidation"}
for L in loads:
    f = min(L + 3, NF - 1)
    row = r[f]
    hot = [(a, int(row[a])) for a in range(0x74c, 0x800) if row[a] != 0]
    s = " ".join(f"{a:03x}{'='+NAMES[a][:12] if a in NAMES else ''}:{v}" for a, v in hot)
    print(f"  row {L:5d} (+3): world={row[WORLD]} lvl={row[LEVEL]} ap=${row[AREA]:02x} | {s[:400]}")
