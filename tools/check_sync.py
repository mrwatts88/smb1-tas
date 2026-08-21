#!/usr/bin/env python3
"""Compare a per-frame emulator dump (tools/lua/wr_dump_*.lua CSV) with the .fm2 it replayed.

Prints: the alignment between fm2 line index (0-based) and dump row i (1-based loop iteration),
the axe frame (first OperMode==2) in both conventions, lag frames before the axe, and every
World/Level/AreaNum/OperMode transition (frame of first appearance). Usage:
  tools/check_sync.py data/wr/fceux_wr.csv data/wr/happylee-supermariobros,warped.fm2
  tools/check_sync.py data/wr/bizhawk_wr.csv data/wr/happylee-supermariobros,warped.fm2 1   # offset given explicitly
"""
import csv, sys
BTN = "RLDUTSBA"  # fm2 column order; packed MSB-first: R=0x80 ... A=0x01 (same as the Lua dumps)

def fm2_pads(path):
    pads = []
    for line in open(path, encoding="utf-8", errors="replace"):
        if not line.startswith("|"):
            continue
        f = line.rstrip("\n").split("|")
        p1 = f[2]
        v = 0
        for k, ch in enumerate(p1[:8]):
            if ch != ".":
                v |= 0x80 >> k
        pads.append(v)
    return pads

def main():
    dump, fm2 = sys.argv[1], sys.argv[2]
    rows = list(csv.DictReader(open(dump)))
    pads = fm2_pads(fm2)
    dpad = [int(r["pad"]) for r in rows]
    n = min(len(pads), len(dpad)) - 64
    # find offset k such that dpad[i] == pads[i - 1 + k] for (almost) all i (rows are 1-based loop iterations)
    best = None
    for k in range(-3, 4):
        mism = sum(1 for i in range(4, n) if 0 <= i - 1 + k < len(pads) and dpad[i] != pads[i - 1 + k])
        if best is None or mism < best[1]:
            best = (k, mism)
    k, mism = best
    print(f"dump rows={len(rows)}  fm2 input lines={len(pads)}")
    if all(v == 0 for v in dpad):
        k = int(sys.argv[3]) if len(sys.argv) > 3 else 1
        print(f"pad column is all zero (BizHawk's joypad.get does not report movie input); using offset k={k} (3rd arg; BizHawk rows are one ahead of FCEUX: k=+1)")
    print(f"alignment: dump row i (1-based) carries fm2 line (i-1{k:+d}) -> fm2 frame n (0-based) is row i=n+1{-k:+d}; mismatching rows={mism} of {n-4}")
    # transitions
    def first(col, val):
        for r in rows:
            if int(r[col]) == val:
                return int(r["i"])
    axe_i = first("OperMode", 2)
    print(f"axe (first OperMode==2): row i={axe_i} -> fm2 0-based frame {axe_i-1+k} (1-based {axe_i+k}); last input in fm2 at 0-based line {max(j for j,p in enumerate(pads) if p)}")
    lag_before = sum(1 for r in rows if int(r["i"]) <= axe_i and int(r["lag"]) == 1)
    print(f"lag frames up to and including the axe row: {lag_before}; lag rows: {[int(r['i']) for r in rows if int(r['lag'])==1 and int(r['i'])<=axe_i]}")
    prev = None
    print("transitions (row i: World-Level AreaNum OperMode/Task GameEngineSub):")
    for r in rows:
        key = (r["World"], r["Level"], r["AreaNum"], r["OperMode"])
        if key != prev:
            print(f"  i={int(r['i']):6d}  W{int(r['World'])+1}-{int(r['Level'])+1} area={int(r['AreaNum']):#04x} OperMode={r['OperMode']}/{r['OperMode_Task']} sub={r['GameEngineSub']} ITC={r['IntervalTimerCtl']} FC={r['FrameCounter']} timer={r['Timer_H']}{r['Timer_T']}{r['Timer_O']}")
            prev = key
    print(f"final row: i={rows[-1]['i']} OperMode={rows[-1]['OperMode']} lagcount={rows[-1]['lagcount']} movie_mode={rows[-1]['movie_mode']}")

if __name__ == "__main__":
    main()
