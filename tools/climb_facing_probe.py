#!/usr/bin/env python3
"""H12 / F268-F269: PlayerFacingDir = 3 (Left+Right) indexes past the end of PutPlayerOnVine's
two adder tables, and what the game does about it.

    SetVXPl: ldy PlayerFacingDir      ; 1 = right, 2 = left ... or 3, which only L+R produces
             adc ClimbXPosAdder-1,y   ; 2-byte table $f9,$07  (ROM $de25)
             lda $06 / bne ExPVne     ; page adder only when the cell is buffer-1 column 0
             adc ClimbPLocAdder-1,y   ; 2-byte table $ff,$00  (ROM $de27)

y = 3 reads one byte PAST each: $ff for the X adder, and FlagpoleYPosData[0] = $18 for the page
adder, i.e. Player_PageLoc := ScreenRight_PageLoc + 24 pages (+6144 px).  The flagpole path forces
facing = 1 before this code; the vine path does not.

The experiment: play the WR, force Left+Right from frame 1226 (1-1's staircase, so facing becomes 3
while Mario is grounded and keeps it while airborne), poke a climbable metatile ($26) into every
column of the block-buffer row his side probe reads, and let the grab fire at frame 1251 -- where
the probe lands in column 0 of block buffer 1 ($06 == 0), so the page adder is live.  Facing is
then poked to 1 and 2 for controls: same trajectory, same cell, only the index differs.

Usage: tools/climb_facing_probe.py [--frame 1251] [--metatile 0x26] [--quiet]
Expected (F268): facing 1 -> page 11 X 249 (x 3065); facing 2 -> page 12 X 7 (x 3079);
                 facing 3 -> page 36 X 255 (x 9471), and one frame later KeepOnscr clamps him
                 back to the screen's LEFT edge at x 2954 (F269).
"""
import argparse
import glob
import os
import subprocess
import tempfile

CORE = "third_party/QuickNES_Core/quicknes_libretro.so"
WR = "data/wr/wr_inputs.bin"
SKIP = 2      # --reset0 --input-skip 2 reproduces the WR (1-1 flagpole climb at core frame 1285)
LR_FROM = 1226
BB1 = 0x500
A = dict(GES=0x0e, ST=0x1d, FACE=0x33, PAGE=0x6d, X=0x86, Y=0xce, SPD=0x57,
         SCR_EDGE_PG=0x71a, SCR_LEFT_X=0x71c)

def harness(rom, inp, frames, ramout, pokes=()):
    cmd = ["./build/harness", CORE, rom, inp, "--frames", str(frames), "--ram", ramout,
           "--reset0", "--input-skip", str(SKIP), "--quiet"]
    for a, v, f in pokes:
        cmd += ["--poke", f"0x{a:x}=0x{v:x}@{f}"]
    subprocess.run(cmd, check=True)
    return open(ramout, "rb").read()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--frame", type=int, default=1251, help="frame the grab fires on")
    ap.add_argument("--metatile", type=lambda s: int(s, 0), default=0x26)
    args = ap.parse_args()
    rom = glob.glob("roms/*.nes")[0]
    F, tmp = args.frame, tempfile.mkdtemp(prefix="climbfacing")
    inp = os.path.join(tmp, "lr.bin")
    b = bytearray(open(WR, "rb").read())
    for f in range(LR_FROM, F + 40):
        b[f + SKIP] = 0xC0                      # Left+Right, nothing else
    open(inp, "wb").write(bytes(b))

    base = harness(rom, inp, F + 50, os.path.join(tmp, "base.ram"))
    g = lambda d, i, k: d[i * 0x800 + A[k]]
    y = (g(base, F - 2, "Y") + 0x20) & 0xF0     # side probe adds $20 to Y for small Mario
    row = (y - 0x20) & 0xFF
    pokes = [(BB1 + row + c, args.metatile, F - 3) for c in range(16)]

    print(f"grab frame {F}; poking ${args.metatile:02x} into block buffer 1 row 0x{row:02x} "
          f"(columns 0-15) after frame {F-3}")
    print(f"  reference (no poke): x {g(base,F,'PAGE')*256+g(base,F,'X')}, "
          f"screen left edge page {g(base,F,'SCR_EDGE_PG')} x {g(base,F,'SCR_LEFT_X')}")
    rows = []
    for face in (None, 1, 2):
        extra = list(pokes) + ([] if face is None else [(A["FACE"], face, F - 3)])
        d = harness(rom, inp, F + 50, os.path.join(tmp, f"f{face}.ram"), extra)
        tag = "3 (L+R, out of table)" if face is None else f"{face} (control)"
        grab = next((i for i in range(F - 3, F + 20) if g(d, i, "ST") == 3), None)
        if grab is None:      # facing 3 can be clamped back out of climbing within the frame
            grab = next(i for i in range(F - 3, F + 20)
                        if g(d, i, "PAGE") * 256 + g(d, i, "X")
                        != g(base, i, "PAGE") * 256 + g(base, i, "X"))
        for i in (grab, grab + 1, grab + 4):
            rows.append((tag if i == grab else "", i, g(d, i, "FACE"), g(d, i, "ST"),
                         g(d, i, "PAGE"), g(d, i, "X"), g(d, i, "PAGE") * 256 + g(d, i, "X"),
                         g(base, i, "PAGE") * 256 + g(base, i, "X")))
    print(f"{'facing':<24}{'frame':>6}{'face':>6}{'state':>7}{'page':>6}{'X':>5}{'x':>8}{'no-poke x':>11}")
    for tag, i, fa, st, pg, x, ax, bx in rows:
        print(f"{tag:<24}{i:>6}{fa:>6}{st:>7}{pg:>6}{x:>5}{ax:>8}{bx:>11}")

if __name__ == "__main__":
    main()
