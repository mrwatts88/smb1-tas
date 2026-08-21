#!/usr/bin/env python3
"""Print selected RAM symbols per frame from a full-RAM dump (data/wr/fceux_wr.ram, 2048 bytes per row,
row i (1-based) = fm2 frame i-1, F25). Symbol addresses are parsed from data/disasm/smbdis.asm, so any
`Name = $addr` symbol can be requested; `Name+n` and raw `$addr` also work.

Usage: tools/ram_trace.py RAMFILE FIRST LAST SYM [SYM ...] [--changes]
  --changes  print a row only when one of the requested values changed (first row always printed)
Example: tools/ram_trace.py data/wr/fceux_wr.ram 7590 7724 ScrollLock WarpZoneControl Enemy_ID+0 --changes
"""
import re
import sys

DISASM = "data/disasm/smbdis.asm"

def load_symbols():
    syms = {}
    for line in open(DISASM, encoding="utf-8", errors="replace"):
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*\$([0-9A-Fa-f]+)\s*(;.*)?$", line)
        if m:
            syms[m.group(1)] = int(m.group(2), 16)
    return syms

def resolve(spec, syms):
    m = re.match(r"^(\$[0-9A-Fa-f]+|[A-Za-z_][A-Za-z0-9_]*)(?:\+(\d+))?$", spec)
    if not m:
        raise SystemExit(f"bad symbol spec {spec!r}")
    base = int(m.group(1)[1:], 16) if m.group(1).startswith("$") else syms[m.group(1)]
    return base + int(m.group(2) or 0)

def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    changes = "--changes" in sys.argv
    ramfile, first, last, specs = args[0], int(args[1]), int(args[2]), args[3:]
    syms = load_symbols()
    addrs = [resolve(s, syms) for s in specs]
    data = open(ramfile, "rb").read()
    assert len(data) % 2048 == 0
    print("row " + " ".join(f"{s}(${a:04X})" for s, a in zip(specs, addrs)))
    prev = None
    for row in range(first, last + 1):
        off = (row - 1) * 2048
        vals = [data[off + a] for a in addrs]
        if changes and vals == prev:
            continue
        prev = vals
        print(f"{row:5d} " + " ".join(f"{v:3d}" for v in vals))

if __name__ == "__main__":
    main()
