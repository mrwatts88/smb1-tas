#!/bin/sh
# N11 — the over-cap detectors (explore classes 20 "ahead of the cap line" and 21 "single-frame step over
# the cap", swim-aware) on the levels N10 did not cover: all five rooms of 8-4 (the only level where one
# frame is the record), 1-2, and both rooms of 4-2.  Fedora box, 3 h each.  Roots as in L7 / L8.
set -e
cd "$(dirname "$0")/../.."
CORE=third_party/QuickNES_Core/quicknes_libretro.so
ROM="roms/Super Mario Bros. (W) [!].nes"
IN=data/wr/wr_inputs.bin
K="--enemycell 0 --xcell 8 --ycell 16 --spdcell 16 --relcell 32"
go() { # go TAG ROOT HORIZON SEED
  systemd-run --user --scope -q -p MemoryMax=1300M --unit "n11-$1" -- \
    ./build/explore "$CORE" "$ROM" "$IN" --root $2 --horizon $3 --anomaly \
    --cells 60000 --rollout 6,50 $K --seed $4 --secs "${SECS:-10800}" --report 300 --out runs/N11-cap-84 \
    > "runs/N11-cap-84/$1.log" 2>&1 &
  echo "launched n11-$1 root=$2 horizon=$3"
}
go r1 15210  800 111   # 8-4 room 1  (control 15224, pipe 15748)
go r2 15905  550 112   # 8-4 room 2  (control 15918, pipe 16185)
go r3 16342  500 113   # 8-4 room 3  (control 16355, pipe 16550; the turnaround)
go r4 16707  950 114   # 8-4 water   (control 16720, side pipe 17416)
go r5 17577  400 115   # 8-4 Bowser  (control 17590, axe 17868)
go w12  2483 1290 116  # 1-2
go w42  6582  700 117  # 4-2 main room
go w42w 7244  520 118  # 4-2 warp-zone room
