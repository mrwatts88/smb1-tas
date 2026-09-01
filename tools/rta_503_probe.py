#!/usr/bin/env python3
"""RTA-1: build the runner's (50,3) mint on the core — a jump from the brick-run top into the left face
of the upper (50,3)-(51,3) pair — and map its windows. Maru's movie (data/wr/maru_inputs.bin) is
used up to its one grounded frame on the run top (row 6898, x 720, speed 40; record 6899 is that
frame's input); everything after is crafted:

  W frames of B+Right on the top (x advances 2.5/frame; the run ends at col 47 = x 768)
  1 frame  B+Left            (last ground frame: facing <- left)
  H frames A+B (+Right from record RB on)   the jump
  then B+Right

usage: tools/rta_503_probe.py [--W a:b] [--H list] [--rb {all,contact,K}] [--tap N] [--air {N,L}] [--frames N]
  --rb all      Right held for the whole jump (phase 1: find contacts)
  --rb contact  Right back on the predicted contact frame (x+13 >= 800 at 2.5 px/frame) minus 1
  --rb K        Right back K frames after takeoff
  --H 0         no jump at all: run off the ledge after the tap, K neutral (B only) frames, then B+Right
Per run: contact (impede) row/y/facing, offset gain (offset 60 rows after takeoff minus 122), and
the outcome: CLEAR = passed over the (50,3) pair (x in [800,831] with feet y <= 48), TOP503 = landed on
it, TOP547 = landed on (54,7), FLOOR = fell to y 176, DEATH. Reading: docs/experiments/RTA-1-maru-42-mint.md."""
import os, subprocess, sys

INPUTS = "data/wr/maru_inputs.bin"
TMP = "runs/RTA-1/tmp"
BIT = {"A": 1, "B": 2, "U": 16, "D": 32, "L": 64, "R": 128}
PREFIX_END = 6899          # records [0, 6899) kept; record 6899 = row 6898's input (grounded, x 720)
ROW0 = 6898                # the grounded row
X0 = 720

TAP = 1                    # --tap N: Left-tap length in frames (0 = control, no tap)
AIR = "N"                  # --air L: hold Left (instead of neutral) during the ascent until Right returns

def byte(s): return sum(BIT[c] for c in s)

def build(base, W, H, rb):
    inp = bytearray(base[:PREFIX_END])
    inp += bytes([byte("BR")] * W)
    inp += bytes([byte("BL")] * TAP) if TAP else bytes([byte("BR")])   # --tap 0: no Left tap (control)
    takeoff_rec = len(inp)                     # first A record
    x_takeoff = X0 + 2.5 * (W + max(TAP, 1))
    contact_after = int((787 - x_takeoff) / 2.5 + 0.999)   # frames after takeoff until x+13 >= 800
    if rb == "all": k = 0
    elif rb == "contact": k = max(0, contact_after - 1)
    else: k = int(rb)
    if H == 0:                                  # no jump: run off the ledge; k = neutral frames after the tap
        inp += bytes([byte("B")] * k)
    for j in range(H): inp += bytes([byte("ABR" if j >= k else ("ABL" if AIR == "L" else "AB"))])
    inp += bytes([byte("BR")] * 200)
    return bytes(inp), takeoff_rec, k

def run(base, W, H, rb, frames):
    os.makedirs(TMP, exist_ok=True)
    inp, trec, k = build(base, W, H, rb)
    name = f"w{W}_h{H}_rb{rb}_t{TAP}_{AIR}"
    p = f"{TMP}/{name}.bin"; open(p, "wb").write(inp)
    ramp = f"{TMP}/{name}.ram"
    subprocess.run(["./build/harness", "third_party/QuickNES_Core/quicknes_libretro.so",
                    "roms/Super Mario Bros. (W) [!].nes", p, "--input-skip", "2", "--reset0",
                    "--frames", str(frames), "--ram", ramp, "--quiet"], check=True, capture_output=True)
    ram = open(ramp, "rb").read(); os.remove(ramp)
    nrows = len(ram) // 2048
    def B(r, a): return ram[(r - 1) * 2048 + a]
    def x(r): return B(r, 0x6d) * 256 + B(r, 0x86)
    def off(r): return x(r) - (B(r, 0x071a) * 256 + B(r, 0x071c))
    t = trec - 1                                # row of the takeoff frame
    lo, hi = t, min(t + 70, nrows)
    imps = [r for r in range(lo, hi) if B(r, 0x0785) == 16]
    contact = (f"impede@{imps[0]-t:2d} y={B(imps[0],0xce):3d} f={B(imps[0],0x33)} n={len(imps)}" if imps
               else "no contact                 ")
    gain = off(min(t + 60, nrows - 1)) - 122
    outcome = "?"
    dead = next((r for r in range(lo, hi) if B(r, 0x0e) == 11), None)
    if dead: outcome = f"DEATH@{dead-t}"
    else:
        for r in range(lo, hi):
            xr, yr, st = x(r), B(r, 0xce), B(r, 0x1d)
            if 800 <= xr <= 831 and yr <= 48 and st == 1: outcome = "CLEAR"; break
            if st == 0 and r > t + 2:
                outcome = {48: "TOP503", 112: "TOP547", 176: "FLOOR"}.get(yr, f"ground y={yr}") + f"@{r-t} x={xr}"
                break
    ymin = min(B(r, 0xce) for r in range(lo, hi))
    print(f"W={W:2d} H={H:2d} tap={TAP} air={AIR} rb={rb:>7s}(k={k:2d}) x0={X0+2.5*(W+max(TAP,1)):6.1f} | {contact} | gain={gain:+3d} ymin={ymin:3d} | {outcome}")
    sys.stdout.flush()

def main():
    global TAP
    a = sys.argv
    if "--tap" in a: TAP = int(a[a.index("--tap") + 1])
    global AIR
    if "--air" in a: AIR = a[a.index("--air") + 1]
    W = a[a.index("--W") + 1] if "--W" in a else "0:18"
    Ws = range(int(W.split(":")[0]), int(W.split(":")[1]) + 1)
    Hs = [int(h) for h in (a[a.index("--H") + 1] if "--H" in a else "12,16,20,24").split(",")]
    rb = a[a.index("--rb") + 1] if "--rb" in a else "all"
    frames = int(a[a.index("--frames") + 1]) if "--frames" in a else 7050
    base = open(INPUTS, "rb").read()
    for H in Hs:
        for w in Ws: run(base, w, H, rb, frames)

if __name__ == "__main__":
    main()
