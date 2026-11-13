#!/usr/bin/env python3
"""Replay an explore path file on the Mac core and print all six enemy slots (id/flag/x/y/state) around a frame.
usage: tools/slot_replay.py PATHFILE FRAME [SPAN]   (stdlib only; all six slots, unlike tools/e3_replay.py)"""
import os, subprocess, sys, tempfile
SP = os.environ.get("SCRATCH") or tempfile.mkdtemp(prefix="slotreplay")
CORE = "third_party/QuickNES_Core/quicknes_libretro.dylib"
if not os.path.exists(CORE): CORE = "third_party/QuickNES_Core/quicknes_libretro.so"
ROM = "roms/smb.nes" if os.path.exists("roms/smb.nes") else "roms/Super Mario Bros. (W) [!].nes"
pf, ctr = sys.argv[1], int(sys.argv[2]); span = int(sys.argv[3]) if len(sys.argv) > 3 else 6
raw = open(pf, "rb").read(); nl = raw.index(b"\n"); hdr = raw[:nl].decode(); body = raw[nl + 1:]
kv = hdr.split(); root = int(kv[kv.index("root") + 1])
print(pf, "\n  header:", hdr, "\n  root", root, "pathlen", len(body))
wr = open("data/wr/wr_inputs.bin", "rb").read()
ip = os.path.join(SP, "slot.bin"); open(ip, "wb").write(wr[:root + 2] + body + bytes(60))
nf = root + len(body) + 60
subprocess.run(["./build/harness", CORE, ROM, ip, "--frames", str(nf), "--input-skip", "2",
                "--ram", os.path.join(SP, "slot.ram"), "--quiet"], check=True, capture_output=True)
d = open(os.path.join(SP, "slot.ram"), "rb").read()
print("  frame     x    y spd st GES world area ap  | slots 0-5: id/flag@x,y(state)")
for f in range(max(0, ctr - span), min(len(d) // 2048, ctr + span + 1)):
    q = d[f * 2048:(f + 1) * 2048]
    x = q[0x6d] * 256 + q[0x86]; y = q[0xb5] * 256 + q[0xce]
    sp = q[0x57] - 256 if q[0x57] > 127 else q[0x57]
    sl = " ".join(f"{q[0x16+s]:02x}/{q[0x0f+s]:x}@{q[0x6e+s]*256+q[0x87+s]},{q[0xcf+s]}({q[0x1e+s]:02x})" for s in range(6))
    print(f"  {f} {x:5d} {y:4d} {sp:4d} {q[0x1d]:2d} {q[0x0e]:3d} {q[0x75f]+1}-{q[0x75c]+1} ${q[0x750]:02x} | {sl}" + (" <<<" if f == ctr else ""))
