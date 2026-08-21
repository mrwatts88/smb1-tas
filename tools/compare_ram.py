#!/usr/bin/env python3
"""Compare two frame-major 2 KiB-per-frame RAM dumps (FCEUX dump vs fast-core output).

Usage: tools/compare_ram.py REF.ram NEW.ram [--offset K] [--search] [--ignore a,b,..] [--from R] [--max N] [--all]
  --all: do not stop at the first mismatch; count mismatching rows and list the first 30 (row, #bytes, addresses)
  REF row r (0-based) is compared with NEW row r+K. --search tries K in -10..10 and reports the K
  with the longest identical prefix. --ignore lists hex addresses or ranges (a-b) to exclude (e.g. the
  never-read uninitialised stack bytes 160-1ff). Prints the first mismatching row with its differing addresses.
"""
import sys

def load(path):
    d = open(path, "rb").read()
    assert len(d) % 2048 == 0, path
    return d

def prefix(ref, new, k, ignore, maxn, start=0):
    nref, nnew = len(ref) // 2048, len(new) // 2048
    n = min(nref, nnew - k if k >= 0 else nnew, maxn)
    for r in range(max(start, -k), n):
        a = ref[r * 2048:(r + 1) * 2048]; b = new[(r + k) * 2048:(r + k + 1) * 2048]
        if a != b:
            diff = [i for i in range(2048) if a[i] != b[i] and i not in ignore]
            if diff:
                return r, diff, a, b
    return n, [], None, None

def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    ref, new = load(args[0]), load(args[1])
    k = 0; search = "--search" in sys.argv; ignore = set(); maxn = 10**9; start = 0
    for i, a in enumerate(sys.argv):
        if a == "--offset": k = int(sys.argv[i + 1])
        if a == "--ignore":
            for x in sys.argv[i + 1].split(","):
                lo, _, hi = x.partition("-")
                ignore.update(range(int(lo, 16), int(hi or lo, 16) + 1))
        if a == "--max": maxn = int(sys.argv[i + 1])
        if a == "--from": start = int(sys.argv[i + 1])
    print(f"ref rows {len(ref)//2048}, new rows {len(new)//2048}")
    if search:
        best = None
        for kk in range(-10, 11):
            r, diff, _, _ = prefix(ref, new, kk, ignore, maxn, start)
            print(f"  offset {kk:3d}: identical rows up to {r}")
            if best is None or r > best[0]: best = (r, kk)
        k = best[1]
        print(f"best offset {k}")
    if "--all" in sys.argv:
        nref, nnew = len(ref) // 2048, len(new) // 2048
        n = min(nref, nnew - k if k >= 0 else nnew, maxn)
        bad = []
        for r in range(max(start, -k), n):
            a = ref[r * 2048:(r + 1) * 2048]; b = new[(r + k) * 2048:(r + k + 1) * 2048]
            if a != b:
                diff = [i for i in range(2048) if a[i] != b[i] and i not in ignore]
                if diff:
                    bad.append((r, diff))
        print(f"compared ref rows {max(start, -k)}..{n-1} at offset {k}: {len(bad)} mismatching rows")
        for r, diff in bad[:30]:
            print(f"  ref row {r} (FCEUX row {r+1}): {len(diff)} bytes: " + " ".join(f"${i:04X}" for i in diff[:12]) + (" ..." if len(diff) > 12 else ""))
        return 1 if bad else 0
    r, diff, a, b = prefix(ref, new, k, ignore, maxn, start)
    if not diff:
        print(f"MATCH: {r} rows identical at offset {k}")
        return 0
    print(f"first mismatch at ref row {r} (0-based; FCEUX row {r+1}) at offset {k}: {len(diff)} bytes")
    for i in diff[:24]:
        print(f"  ${i:04X}: ref {a[i]:3d} new {b[i]:3d}")
    return 1

if __name__ == "__main__":
    sys.exit(main())
