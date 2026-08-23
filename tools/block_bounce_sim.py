# Block-object bounce (BumpBlock + ImposeGravityBlock per frame): return frame for every leftover YMF_Dummy value
def sim(dummy, maxspd):
    y, spd, force = 0x00, 0xfe, 0x00   # y low byte relative (block at y&0xf0), speed -2, move force 0
    for f in range(1, 40):
        # ImposeGravity: dummy += force (carry c); y += spd + c; then force += 0x50; spd += carry(force)
        t = dummy + force; c = t >> 8; dummy = t & 0xff
        y = (y + spd + c) & 0xff
        force2 = force + 0x50; c2 = force2 >> 8; force = force2 & 0xff
        spd = (spd + c2) & 0xff
        # cap: if spd >= max (signed compare) and force >= 0x80 -> spd = max, force = 0 ... (ImposeGravity tail)
        s = spd - 256 if spd >= 128 else spd
        m = maxspd - 256 if maxspd >= 128 else maxspd
        if s >= m and force >= 0x80: spd = maxspd & 0xff; force = 0
        if (y & 0x0f) < 5: return f, dummy
    return None, dummy
import sys
maxspd = int(sys.argv[1], 16) if len(sys.argv) > 1 else 0x06
res = {}
for d in range(256):
    f, _ = sim(d, maxspd)
    res.setdefault(f, []).append(d)
for f, ds in sorted(res.items(), key=lambda kv: (kv[0] is None, kv[0])): print("return frame", f, "for", len(ds), "dummy values", ds[:6], "...")
