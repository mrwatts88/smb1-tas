#!/usr/bin/env python3
"""N7 poke lab: does the speed-keeping wall entry (F244: moving direction LEFT, x speed >= 1, feet >= 5 px
into a tile => no impede and no side check) carry Mario into a wall face at full speed?
After core frame F of a movie, poke Player_Y_Position / Y speed 0 / moving direction 2, feed no input,
and report whether the left side point ends up inside a non-empty tile at speed, and how far x gets.

usage: tools/clip_poke_lab.py INPUTS.bin F0 F1 Y0 Y1 [--mdir 2] [--frames 60] [--yspd 0]
"""
import os, subprocess, sys
CORE = "third_party/QuickNES_Core/quicknes_libretro.dylib"
if not os.path.exists(CORE): CORE = "third_party/QuickNES_Core/quicknes_libretro.so"
ROM = "roms/smb.nes" if os.path.exists("roms/smb.nes") else "roms/Super Mario Bros. (W) [!].nes"
TMP = "runs/N7-w42-stairs/tmp"
def opt(name, default):
    return int(sys.argv[sys.argv.index(name) + 1], 0) if name in sys.argv else default
def main():
    inp = bytearray(open(sys.argv[1], "rb").read())
    F0, F1, Y0, Y1 = (int(v) for v in sys.argv[2:6])
    mdir, nfr, yspd = opt("--mdir", 2), opt("--frames", 60), opt("--yspd", 0)
    os.makedirs(TMP, exist_ok=True)
    for F in range(F0, F1 + 1):
        for Y in range(Y0, Y1 + 1):
            ed = bytearray(inp); ed[F + 3:F + 3 + nfr] = bytes(nfr)          # no input after frame F (file index = frame + 2)
            p = f"{TMP}/lab.bin"; open(p, "wb").write(ed)
            subprocess.run(["./build/harness", CORE, ROM, p, "--input-skip", "2", "--reset0", "--frames", str(F + nfr + 1),
                            "--ram", f"{TMP}/lab.ram", "--quiet",
                            "--poke", f"0xce={Y}@{F}", "--poke", f"0x9f={yspd & 255}@{F}", "--poke", f"0x433=0@{F}",
                            "--poke", f"0x416=0@{F}", "--poke", f"0x45={mdir}@{F}"], check=True, capture_output=True)
            d = open(f"{TMP}/lab.ram", "rb").read(); b = lambda i, a: d[i * 2048 + a]
            x0 = b(F, 0x6d) * 256 + b(F, 0x86); emb = None; line = []
            for f in range(F + 1, F + nfr):
                x = b(f, 0x6d) * 256 + b(f, 0x86); y = b(f, 0xce); sp = b(f, 0x57); sp = sp - 256 if sp > 127 else sp
                col, row = (x + 2) >> 4, (y + 24 - 32) >> 4
                cell = b(f, 0x500 + ((col >> 4) & 1) * 0xd0 + row * 16 + (col & 15)) if 0 <= row < 13 and b(f, 0xb5) == 1 else 0
                if cell and sp >= 20 and emb is None: emb = (f, x, y, sp, col, row)
                if f - F <= 12: line.append(f"{x}/{y}/{sp}{'*' if cell else ''}")
            xe = b(F + nfr - 1, 0x6d) * 256 + b(F + nfr - 1, 0x86); ye = b(F + nfr - 1, 0xce)
            print(f"F {F} x {x0} Y {Y}: {'EMBEDDED at speed ' + str(emb) if emb else 'no'}; after {nfr} frames x {xe} y {ye} | " + " ".join(line))
if __name__ == "__main__":
    main()
