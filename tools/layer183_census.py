#!/usr/bin/env python3
"""Count run-4 layer-183 records in the stairs-top handoff window.
Record: 16 bytes; compressed key starts with x_pos>>4 as 16 bits, LSB-first bitpack
=> candidate A: x16 = b0 | b1<<8 (LSB-first fills byte 0 low bits first)
   candidate B: x16 = b0<<8 | b1 (byte-order fallback)
Validation: log says layer 183 max x = 0xbd790 => max x16 must be 0xbd79.
Counts x_pos >= 0xbd000 (x >= 3024 px, the stairs-top window) + a top histogram."""
import sys
import numpy as np

path = sys.argv[1]
REC = 16
CHUNK = 4_000_000 * REC  # 64 MB per chunk
maxA = 0
maxB = 0
n = 0
count_3024_A = 0
count_3008_A = 0
hist = {}
with open(path, 'rb') as f:
    while True:
        buf = f.read(CHUNK)
        if not buf:
            break
        a = np.frombuffer(buf, dtype=np.uint8)
        a = a[: (len(a) // REC) * REC].reshape(-1, REC)
        n += a.shape[0]
        b0 = a[:, 0].astype(np.uint32)
        b1 = a[:, 1].astype(np.uint32)
        xA = b0 | (b1 << 8)
        xB = (b0 << 8) | b1
        maxA = max(maxA, int(xA.max()))
        maxB = max(maxB, int(xB.max()))
        count_3024_A += int((xA >= 0xbd0).sum() - (xA >= 0xbd0).sum())  # placeholder, fixed below
        # x16 = x_pos>>4; x_pos in 1/256 px units => px = x16>>4 ... careful:
        # x_pos = x16<<4 ; px = x_pos/256 = x16/16. x >= 3024 px => x16 >= 3024*16 = 48384 = 0xbd00
        count_3024_A += int((xA >= 0xbd00).sum())
        count_3008_A += int((xA >= 0xbc00).sum())
        top = xA[xA >= 0xbc00]
        px = (top // 16).astype(np.int32)
        for v, c in zip(*np.unique(px // 8 * 8, return_counts=True)):
            hist[int(v)] = hist.get(int(v), 0) + int(c)
print(f'records: {n}')
print(f'candidate A max x16: {maxA:#x} (expect 0xbd79)   candidate B max x16: {maxB:#x}')
print(f'A: count x >= 3024 px (x16 >= 0xbd00): {count_3024_A}')
print(f'A: count x >= 3008 px (x16 >= 0xbc00): {count_3008_A}')
print('A: histogram of x >= 3008, 8-px buckets (px_bucket: states):')
for k in sorted(hist):
    print(f'  {k}: {hist[k]}')
