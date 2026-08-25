#!/usr/bin/env python3
"""Replay a Track E path file on the QuickNES core and print the trajectory around a frame.

Path files are written by build/explore: a text header line (root, len, and whatever the mode
records) then `len` raw NES-order input bytes to feed from core frame `root` onward.

Usage: tools/e3_replay.py PATHFILE [--inputs FILE] [--around FRAME] [--span N] [--extra N]
"""
import os, subprocess, sys
import numpy as np

SP = os.environ.get("SCRATCH", "/tmp/claude-1000/-home-mattwatts-Documents-smb1-tas/"
                                "34855d8b-c5d3-4b37-b00d-fca2485f383c/scratchpad")
CORE = "third_party/QuickNES_Core/quicknes_libretro.so"
ROM = "roms/Super Mario Bros. (W) [!].nes"

def main():
    path_file = sys.argv[1]
    opts = dict(inputs="data/wr/wr_inputs.bin", around=None, span=40, extra=120)
    a = sys.argv[2:]
    for i in range(0, len(a) - 1, 2):
        opts[a[i][2:]] = a[i + 1]
    raw = open(path_file, "rb").read()
    nl = raw.index(b"\n")
    hdr = raw[:nl].decode()
    body = raw[nl + 1:]
    kv = hdr.split()
    root = int(kv[kv.index("root") + 1])
    print(f"{path_file}\n  header: {hdr}\n  root={root} pathlen={len(body)}")

    wr = bytearray(open(opts["inputs"], "rb").read())
    inputs = bytes(wr[:root + 2]) + body + bytes(int(opts["extra"]))
    ip = os.path.join(SP, "e3replay.bin"); open(ip, "wb").write(inputs)
    nf = root + len(body) + int(opts["extra"])
    subprocess.run(["./build/harness", CORE, ROM, ip, "--frames", str(nf),
                    "--input-skip", "2", "--ram", os.path.join(SP, "e3replay.ram"), "--quiet"],
                   check=True, capture_output=True)
    r = np.memmap(os.path.join(SP, "e3replay.ram"), dtype=np.uint8, mode="r").reshape(-1, 2048)
    ctr = int(opts["around"]) if opts["around"] else root + len(body)
    span = int(opts["span"])
    print("  frame     x    y spd yspd st GES ap entr alt world size  $300 AddrCtrl  enemies")
    for f in range(max(0, ctr - span), min(r.shape[0], ctr + span)):
        q = r[f].astype(int)
        x = q[0x6d] * 256 + q[0x86]; y = q[0xb5] * 256 + q[0xce]
        sp = q[0x57] - 256 if q[0x57] > 127 else q[0x57]
        ys = q[0x9f] - 256 if q[0x9f] > 127 else q[0x9f]
        ens = " ".join(f"{q[0x16+s]:02x}@{q[0x87+s]}" for s in range(5) if q[0x16 + s])
        mark = " <<<" if f == ctr else ""
        print(f"  {f} {x:5d} {y:4d} {sp:4d} {ys:4d} {q[0x1d]:2d} {q[0x0e]:3d} ${q[0x750]:02x} "
              f"{q[0x751]:4d} {q[0x752]:3d} {q[0x75f]:5d} {q[0x754]:4d} {q[0x300]:5d} {q[0x773]:7d}  {ens}{mark}")

main()
