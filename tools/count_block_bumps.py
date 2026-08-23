import glob, os, re, subprocess, sys
d, root, ln = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
cells = {}; nb = 0; used = set(); restores_late = 0
for f in sorted(glob.glob(d + '/m*.bin')):
    out = subprocess.run(['third_party/smb-opt/target/release/smb-opt', 'tracec', 'W42Main', f, '6584', str(root - 6584 + ln), '--lift', '0'], capture_output=True, text=True).stdout
    prev = 0; bumped = False
    for line in out.splitlines():
        m = re.match(r'^blocks: bounce (\d+) used (0x[0-9a-f]+)', line)
        if not m: continue
        b = int(m.group(1)); u = int(m.group(2), 16)
        if b and b != prev:
            v = b - 1; cells[(v >> 4, v & 15)] = cells.get((v >> 4, v & 15), 0) + 1; bumped = True
        prev = b
        if u: used.add(u)
    nb += bumped
print(f"{d}: {nb} trials with a fresh bump; cells bumped: {sorted(cells.items())}; used masks seen: {[hex(u) for u in sorted(used)]}")
