#!/usr/bin/env python3
"""Print Mario and the six enemy slots from a QuickNES RAM dump (2048 bytes per frame, as written by build/harness
--ram / tools/model_difftest.py --keep) for a range of frames — the core-side view for enemy-module debugging
(P2.5c-2). Addresses from smbdis.asm.

usage: tools/ram_slots.py DUMP.ram FIRST LAST [--all]   (--all: also empty slots)"""
import sys

E = dict(flag=0x0F, id=0x16, state=0x1E, xspd=0x58, page=0x6E, x=0x87, yspd=0xA0, yhi=0xB6, y=0xCF, dir=0x46,
         force=0x0401, cbits=0x0491, ftimer=0x078A, itimer=0x079A, ydum=0x0433)

def main():
    a = sys.argv[1:]
    if len(a) < 3: print(__doc__); sys.exit(2)
    data = open(a[0], "rb").read(); lo, hi = int(a[1]), int(a[2]); allslots = "--all" in a
    for f in range(lo, hi + 1):
        r = data[f * 2048:(f + 1) * 2048]
        if len(r) < 2048: break
        px = (r[0x6D] << 8) | r[0x86]; py = r[0xCE]; ys = r[0x9F] - 256 if r[0x9F] >= 128 else r[0x9F]
        line = (f"f{f} GES {r[0x0E]} M x{px} Y{py} ys{ys} st{r[0x1D]} fc{r[0x09]:02x} stomp{r[0x0791]} inj{r[0x079E]} "
                f"pcb{r[0x0490]:02x} scr{(r[0x071A] << 8) | r[0x071C]}")
        for i in range(6):
            if not allslots and r[E["flag"] + i] == 0: continue
            ex = (r[E["page"] + i] << 8) | r[E["x"] + i]
            line += (f" | s{i} fl{r[E['flag'] + i]} id{r[E['id'] + i]:02x} st{r[E['state'] + i]:02x} x{ex} y{r[E['y'] + i]}"
                     f" yh{r[E['yhi'] + i]} spd{r[E['xspd'] + i]:02x} f{r[E['force'] + i]:02x} d{r[E['dir'] + i]}"
                     f" it{r[E['itimer'] + i]} ft{r[E['ftimer'] + i]} cb{r[E['cbits'] + i]:02x} ys{r[E['yspd'] + i]:02x}")
        print(line)

if __name__ == "__main__":
    main()
