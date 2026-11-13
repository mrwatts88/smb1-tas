#!/bin/sh
# L8b — the stretches L8 (runs/L8-e6-objectlens) did not cover, same binary, same flags, same lens.
# L8's roots/horizons were E6's: they stop before 1-1's pipe, before 4-2's warp-zone room, and 25-50
# frames before the flagpole in 4-1 and 8-3; 8-1 was never in the set.  Roots below are the first
# controllable frame of each room on the WR line (tools/route_viewer.py on the WR movie).
set -e
cd "$(dirname "$0")/../.."
CORE=third_party/QuickNES_Core/quicknes_libretro.so
ROM="roms/Super Mario Bros. (W) [!].nes"
IN=data/wr/wr_inputs.bin
K="--enemycell 0 --xcell 8 --ycell 16 --spdcell 16 --relcell 32"
go() { # go TAG ROOT HORIZON SEED SECS
  systemd-run --user --scope -q -p MemoryMax=1500M --unit "l8b-$1" -- \
    ./build/explore "$CORE" "$ROM" "$IN" --root $2 --horizon $3 \
    --max-addr 0x300 --max-weight 20 --prog-fw 1 --anomaly \
    --cells 80000 --rollout 6,50 $K --seed $4 --secs $5 --report 300 --out runs/L8b-gaps \
    > "runs/L8b-gaps/$1.log" 2>&1 &
  echo "launched l8b-$1 root=$2 horizon=$3 secs=$5"
}
go w81     7930 2500 81 21600   # 8-1 whole level, through the flagpole (grab 10340)
go w11coin  652  140 82  3600   # 1-1 coin room (control 652..762)
go w11tail 1045  400 83  7200   # 1-1 after the pipe, through the flagpole (grab 1284) and the walk-off
go w42warp 7244  520 84  7200   # 4-2 warp-zone room (control 7244..7719)
go w41end  5250  300 85  7200   # 4-1 last screens through the flagpole (grab 5420)
go w83end 14330  300 86  7200   # 8-3 last screens through the flagpole (grab 14485)
