#!/usr/bin/env python3
"""Census / hand-pick of goal parents in a bfscx layer file (P2.3c-2c seam discipline: never trust the
auto-pick "best by (x speed, x)" — it found the sky twice and a fated arc three times).

Scans a 96-byte-record layer file (20-byte key + 64-byte ext + padding; older 24-byte files: --stride 24)
and prints the top candidates among the states whose child under R crosses the goal x, decoded from the
validated LSB-first BitPack key layout (layer-183 census):
  bits 0-15   x16  = x_pos >> 4          (bytes 0-1, little)
  bits 16-31  y16  = y_pos - 0xd000      (bytes 2-3, little)
  bits 32-44  xs13 = x_spd >> 2          (b4 | (b5 & 0x1f) << 8)
  bits 45-56  ys12 = y_spd (12-bit two's complement)
  bits 57-58  ps   = player_state        0 = STANDING, 1 = JUMPING, 2 = FALLING

usage: tools/pick_parent.py LAYER_FILE GOAL_X_PX [--ymin Y] [--ymax Y] [--standing | --descending | --rising]
                            [--stride N] [--top K] [--rank ykey]
  GOAL_X_PX   the segment's --goal-x; the crossing band is x_pos in [goal - 0x290, goal) (one frame of 2.5 px)
  --ymin/--ymax  pixel Y band (screen coordinates; Y = y_pos/256 - 256; the ceiling top is Y <= 0 = the sky)
  --standing / --descending / --rising   player-state / y-speed filter
  --rank ykey    'low' (largest Y first), 'high' (smallest Y first), default: max x speed then Y-low
Prints decoded fields and the full record list (paste into `smb-opt bfscx-path … STEP "[..]" 0x80`).
"""
import sys

def main():
    a = sys.argv[1:]
    if len(a) < 2:
        print(__doc__); sys.exit(2)
    path, goal_x = a[0], int(a[1]); ymin = -1000; ymax = 1000; want = None; stride = 96; top = 8; rank = 'speed'
    i = 2
    while i < len(a):
        if a[i] == '--ymin': ymin = int(a[i + 1]); i += 2
        elif a[i] == '--ymax': ymax = int(a[i + 1]); i += 2
        elif a[i] == '--stride': stride = int(a[i + 1]); i += 2
        elif a[i] == '--top': top = int(a[i + 1]); i += 2
        elif a[i] == '--rank': rank = a[i + 1]; i += 2
        elif a[i] in ('--standing', '--descending', '--rising'): want = a[i][2:]; i += 1
        else: raise SystemExit(f'unknown option {a[i]}')
    gx = goal_x << 8
    lo16, hi16 = (gx - 0x290) >> 4, gx >> 4
    cands = []; n = 0; band = 0
    chunk = 1_000_000 * stride
    with open(path, 'rb') as f:
        while True:
            buf = f.read(chunk)
            if not buf: break
            m = (len(buf) // stride) * stride
            for off in range(0, m, stride):
                r = buf[off:off + stride]
                x16 = r[0] | r[1] << 8
                if x16 < lo16 or x16 >= hi16: continue
                band += 1
                y_pos = (r[2] | r[3] << 8) + 0xd000
                Y = y_pos / 256 - 256
                if Y < ymin or Y > ymax: continue
                xs = (r[4] | (r[5] & 0x1f) << 8) << 2
                ys = (r[5] >> 5) | (r[6] << 3) | ((r[7] & 1) << 11)
                if ys >= 0x800: ys -= 0x1000
                ps = (r[7] >> 1) & 3
                if want == 'standing' and ps != 0: continue
                if want == 'descending' and not (ps != 0 and ys > 0): continue
                if want == 'rising' and not (ps != 0 and ys < 0): continue
                cands.append((xs, Y, x16, ys, ps, bytes(r)))
            n += m // stride
    if rank == 'low': cands.sort(key=lambda t: (t[1], t[0]), reverse=True)
    elif rank == 'high': cands.sort(key=lambda t: (-t[1], t[0]), reverse=True)
    else: cands.sort(key=lambda t: (t[0], t[1]), reverse=True)
    print(f'scanned {n} records; {band} in the crossing band x in [{lo16 << 4:#x}, {hi16 << 4:#x}); {len(cands)} pass the filters')
    for xs, Y, x16, ys, ps, r in cands[:top]:
        print(f'x={(x16 << 4) / 256:.2f} Y={Y:.2f} x_spd={xs:#x} ({xs / 256:.2f}px/f) y_spd={ys / 256:.2f} ps={["STAND", "JUMP", "FALL", "?"][ps]}')
        print(list(r))

if __name__ == '__main__':
    main()
