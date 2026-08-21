#!/usr/bin/env python3
"""Compare two per-frame dumps (CSV from tools/lua/wr_dump_*.lua) row by row on game-state columns.

Reports per-column first divergence, total differing rows, and lag-row differences. Rows are
matched by `i` (1-based loop iteration = fm2 frame i-1 when the pad column aligns at offset 0).
Usage: tools/compare_dumps.py data/wr/fceux_wr.csv data/wr/bizhawk_wr.csv [--cols a,b,c] [--offset 1]
(BizHawk dumps are one row ahead of FCEUX dumps: use --offset 1 with FCEUX as A.)
"""
import argparse, csv
DEFAULT = "pad,OperMode,OperMode_Task,GameEngineSub,World,Level,AreaNum,IntervalTimerCtl,FrameCounter,TimerCtl,Player_PageLoc,Player_X,Player_Y,Player_State,PlayerStatus,ScreenLeft_Page,Timer_H,Timer_T,Timer_O,RNG0,RNG1,Player_X_Speed,EnemyFrameTimer"

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("a"); ap.add_argument("b"); ap.add_argument("--cols", default=DEFAULT); ap.add_argument("--offset", type=int, default=0, help="compare A row i+offset with B row i")
    args = ap.parse_args()
    A = {int(r["i"]) - args.offset: r for r in csv.DictReader(open(args.a))}
    B = {int(r["i"]): r for r in csv.DictReader(open(args.b))}
    print(f"(A rows re-indexed by -{args.offset}: A row i+{args.offset} is compared with B row i)")
    common = sorted(set(A) & set(B))
    print(f"{args.a}: {len(A)} rows; {args.b}: {len(B)} rows; common rows: {len(common)} (i={common[0]}..{common[-1]})")
    cols = args.cols.split(",")
    for c in cols:
        diffs = [i for i in common if A[i][c] != B[i][c]]
        if diffs:
            i0 = diffs[0]
            print(f"  {c:18s} differs on {len(diffs):6d} rows; first at i={i0} ({A[i0][c]} vs {B[i0][c]})")
        else:
            print(f"  {c:18s} identical on all common rows")
    la = [i for i in common if A[i]["lag"] == "1"]; lb = [i for i in common if B[i]["lag"] == "1"]
    print(f"lag rows A ({len(la)}): {la}")
    print(f"lag rows B ({len(lb)}): {lb}")
    for name, rows in (("A", A), ("B", B)):
        v = next((i for i in sorted(rows) if rows[i]["OperMode"] == "2"), None)
        print(f"first OperMode==2 in {name}: i={v}")

if __name__ == "__main__":
    main()
