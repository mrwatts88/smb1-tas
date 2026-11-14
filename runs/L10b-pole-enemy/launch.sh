#!/bin/sh
# L10b — can any stompable enemy be next to the 8-3 flagpole when Mario gets there?  (H57 via an
# enemy bounce, the way the WR's own 8-2 ends.)  Same sweep as L8 plus anomaly class 19
# ("stompable enemy at the flagpole", explore.c).  Controls: silent on 8-2 from root 12300
# (calibrated off, the WR does it), fires there with POLE_NOCAL=1.
set -e
cd "$(dirname "$0")/../.."
CORE=third_party/QuickNES_Core/quicknes_libretro.so
ROM="roms/Super Mario Bros. (W) [!].nes"
IN=data/wr/wr_inputs.bin
K="--enemycell 0 --xcell 8 --ycell 16 --spdcell 16 --relcell 32"
go() { # go TAG ROOT HORIZON SEED SECS
  systemd-run --user --scope -q -p MemoryMax=1500M --unit "l10b-$1" -- \
    ./build/explore "$CORE" "$ROM" "$IN" --root $2 --horizon $3 \
    --max-addr 0x300 --max-weight 20 --prog-fw 1 --anomaly \
    --cells 80000 --rollout 6,50 $K --seed $4 --secs $5 --report 300 --out runs/L10b-pole-enemy \
    > "runs/L10b-pole-enemy/$1.log" 2>&1 &
  echo "launched l10b-$1 root=$2 horizon=$3 secs=$5"
}
go whole_a 13110 1450 91 21600   # 8-3 from the first control frame through the pole
go whole_b 13110 1450 92 21600   # second seed
go koopa   13900  660 93 21600   # from just before the green koopa (page 8 col 9, x 2192)
go koopa_b 13900  660 94 21600   # second seed
go hbros   14200  360 95 21600   # from just before the last two hammer bros (x 2832, 2960)
go hbros_b 14200  360 96 21600   # second seed
