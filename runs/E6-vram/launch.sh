#!/bin/sh
# E6 / P3.4 — the novelty sweep, plus a machine-check of the VRAM-offset ceiling, on the real core.
#
# (1) --max-addr 0x300 maximises VRAM_Buffer1_Offset.  Offset 227 reaches Block_BBuf_Low $03e6,
#     which would redirect a deferred block write to $06D6 WarpZoneControl.  Writing 6 there in
#     1-2 gives WarpZoneNumbers row 6 = {8,7,6} -> world 8 direct, skipping 4-1 and 4-2 (~3,957
#     frames).  That is the largest prize on the board and the only surviving form of H7(c):
#     F235 shows the LEGITIMATE path to WZC 6 is closed (row 6 needs AreaType 1 and 1-2 is
#     permanently underground).  The WR's own max offset is 67, and only during the end-of-level
#     cutscene; 44 during play (F234).
#
# (2) --anomaly is P3.4, never run before.  It reports the first occurrence of each (class, VALUE)
#     pair the WR's own line through the same region never produces -- the allowed sets are learned
#     during --seed-wr, so it is calibrated, not guessed.  17 classes, including WorldNumber,
#     AreaPointer, WarpZoneControl, out-of-table Enemy_ID, EnemyFrenzyBuffer, and a general
#     clip/teleport detector (a position jump larger than physics allows).  Every hit dumps its
#     path; replay any of them with tools/e3_replay.py.
#
# NOTE on the logs: the WORLD 8 banner fires only on WorldNumber == 7.  WorldNumber 35 is the
# Minus World (H6, refuted at table level) and is labelled as such.
set -e
cd "$(dirname "$0")/../.."
CORE=third_party/QuickNES_Core/quicknes_libretro.so
ROM="roms/Super Mario Bros. (W) [!].nes"
IN=data/wr/wr_inputs.bin
S="${SECS:-21600}"
K="--enemycell 0 --xcell 8 --ycell 16 --spdcell 16 --relcell 32"
go() { # go TAG ROOT HORIZON SEED
  systemd-run --user --scope -q -p MemoryMax=1500M --unit "e6-$1" -- \
    ./build/explore "$CORE" "$ROM" "$IN" --root $2 --horizon $3 \
    --max-addr 0x300 --max-weight 20 --prog-fw 1 --anomaly \
    --cells 80000 --rollout 6,50 $K --seed $4 --secs "$S" --report 300 --out runs/E6-vram \
    > "runs/E6-vram/$1.log" 2>&1 &
  echo "launched e6-$1 root=$2 horizon=$3"
}
go w12 2483 1290 71     # 1-2  — where WarpZoneControl matters; wall clip, warp zone, coins, bricks
go w42 6582  700 72     # 4-2  — densest block/vine/item level on the route
go w11  193  380 73     # 1-1  — short, block-dense, holds the known wall-entry sites
go w41 3920 1450 74     # 4-1  — never searched by anyone (F225: 97% at cap, so novelty only)
go w82 10970 2000 75    # 8-2  — never searched; 213 off-cap frames, bullet bills
go w83 13110 1350 76    # 8-3  — never searched; hammer bros are the only RNG-coupled objects here
