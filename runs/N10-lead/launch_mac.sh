#!/bin/sh
# N10 — is Mario ever AHEAD of the record's own line?  explore --anomaly with class 20 ("ahead of the
# reference line", 1/16 px).  In 4-1, 8-1 and 8-3 the record is at the speed cap from the start ramp to the
# pole (F225), so a lead that survives the ramp is an over-cap displacement (H47).  Controls 2026-11-13:
# 4-2 root 6582 fires (the record waits at the mint, lead up to 81 px); 4-1's first 400 frames give 2/16 px
# inside the start ramp.  Runs on the Mac (dylib core), 3 h each, kept awake by caffeinate.
cd "$(dirname "$0")/../.."
CORE=third_party/QuickNES_Core/quicknes_libretro.dylib
ROM=roms/smb.nes
K="--enemycell 0 --xcell 8 --ycell 16 --spdcell 16 --relcell 32"
go() { # go TAG ROOT HORIZON SEED
  nohup caffeinate -i ./build/explore "$CORE" "$ROM" data/wr/wr_inputs.bin --root $2 --horizon $3 \
    --anomaly --cells 80000 --rollout 6,50 $K --seed $4 --secs "${SECS:-10800}" --report 300 --out runs/N10-lead \
    > "runs/N10-lead/$1.log" 2>&1 &
  echo "launched $1 root=$2 horizon=$3"
}
go w41     3978 1450 101   # 4-1 whole level to the pole
go w81     7930 2420 102   # 8-1 whole level to the pole
go w83    13119 1370 103   # 8-3 whole level to the pole
go w11t    1045  245 104   # 1-1 after the pipe to the pole
go w11a     193  370 105   # 1-1 room 1
go w82a   10976 1300 106   # 8-2 up to the wall
