#!/usr/bin/env python3
"""RTA-1: perturbation probe on Maru's 4-2 second mint (the (54,7) left-face mint, fm2 records
6938-6957). Each variant is a list of (record, buttons) edits on the movie's input stream; every
variant is replayed from power-on on the QuickNES core (~1.2 s each) and one line reports: the
impede (SideCollisionTimer set to 16), Mario's y and facing on the contact row, the offset after
the mint, the pipe-entry state, and where the next level load goes (W8-1 = the wrong warp worked).

Run from the repo root on a host with build/harness, the ROM and data/wr/maru_inputs.bin
(python3 tools/fm2_to_inputs.py data/wr/maru-rtarules.fm2 data/wr/maru_inputs.bin).
usage: tools/rta_mint_probe.py [--set base|facing|jump|right|all]   (default all)
Results and reading: docs/experiments/RTA-1-maru-42-mint.md."""
import os, subprocess, sys

INPUTS = "data/wr/maru_inputs.bin"
TMP = "runs/RTA-1/tmp"
BIT = {"A": 1, "B": 2, "U": 16, "D": 32, "L": 64, "R": 128}   # harness order (NES bit order)

def byte(s): return sum(BIT[c] for c in s)

def run(base, name, edits):
    os.makedirs(TMP, exist_ok=True)
    inp = bytearray(base)
    for rec, btn in edits: inp[rec] = byte(btn)
    p = f"{TMP}/{name}.bin"; open(p, "wb").write(inp)
    ramp = f"{TMP}/{name}.ram"
    subprocess.run(["./build/harness", "third_party/QuickNES_Core/quicknes_libretro.so",
                    "roms/Super Mario Bros. (W) [!].nes", p, "--input-skip", "2", "--reset0",
                    "--frames", "7800", "--ram", ramp, "--quiet"], check=True, capture_output=True)
    ram = open(ramp, "rb").read(); os.remove(ramp)
    def B(r, a): return ram[(r - 1) * 2048 + a]
    def x(r): return B(r, 0x6d) * 256 + B(r, 0x86)
    def off(r): return x(r) - (B(r, 0x071a) * 256 + B(r, 0x071c))
    imps = [r for r in range(6930, 6990) if B(r, 0x0785) == 16]
    impede = (f"impedes={len(imps)}@{imps[0]} y={B(imps[0],0xce)} face={B(imps[0],0x33)}" if imps
              else f"no impede (y@6952={B(6952,0xce)})")
    ent = next((r for r in range(7100, 7400) if B(r, 0x0e) == 3), None)
    entry = "no pipe entry" if ent is None else f"entry@{ent} x={x(ent)} off={off(ent)} xscr={B(ent,0x06ff)}"
    dead = next((r for r in range(6930, 7400) if B(r, 0x0e) == 11), None)
    load = next((r for r in range(6930, 7800) if (B(r, 0x075f), B(r, 0x075c)) != (3, 1)), None)
    dest = f"W{B(load,0x075f)+1}-{B(load,0x075c)+1}@{load}" if load else "warp FAILED"
    if dead: dest = f"DEATH@{dead} " + dest
    print(f"{name:13s} {impede:34s} off@6990={off(6990):3d} | {entry:36s} | {dest}")
    sys.stdout.flush()

def variants(which):
    V = [("base", [])]
    if which in ("facing", "all"):
        V += [("noLtap_R", [(6938, "BR")]),            # facing right at the impede
              ("noLtap_neut", [(6938, "B")]),
              ("Ltap_2f", [(6937, "BL"), (6938, "BL")]),
              ("tap-2", [(6937, "BL"), (6938, "BR")]),  # Right on the last ground frame re-flips facing
              ("tap-1+2", [(6937, "BL")])]
    if which in ("jump", "all"):
        # shift Left tap + A block by k; Right returns at 6951 as in the movie (contact is time-fixed at speed 40)
        for k in (-3, -2, -1, 1, 2, 3):
            e = [(6938, "BR")] + [(r, "BR") for r in range(6939, 6958)]
            for r in range(6939 + k, 6958 + k): e.append((r, "ABR" if r >= 6951 else "AB"))
            e.append((6938 + k, "BL"))                # last, so nothing clobbers the tap
            V.append((f"jump{k:+d}", e))
    if which in ("right", "all"):
        for rr in (6945, 6948, 6950, 6952, 6953, 6955):
            V.append((f"Rback@{rr}", [(r, "AB") for r in range(6939, 6958)] + [(r, "ABR") for r in range(rr, 6958)]))
        V.append(("R_allair", [(r, "ABR") for r in range(6939, 6958)]))
    return V

def main():
    which = sys.argv[sys.argv.index("--set") + 1] if "--set" in sys.argv else "all"
    base = open(INPUTS, "rb").read()
    for name, edits in variants(which): run(base, name, edits)

if __name__ == "__main__":
    main()
