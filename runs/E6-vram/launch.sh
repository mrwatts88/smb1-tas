#!/bin/sh
# E6 — two jobs in one run, both on the real core:
#  (1) machine-check F221/F234: how high can VRAM_Buffer1_Offset ($0300) actually go?  Offset 227
#      reaches Block_BBuf_Low $03e6, which would redirect a deferred block write to $06D6
#      WarpZoneControl -- in 1-2 that is world 8 direct, skipping 4-1 and 4-2 (~3,957 frames).
#      The WR's max is 67, and only during the end-of-level cutscene; 44 during play (F234).
#  (2) P3.4, the novelty sweep, never run before: --anomaly reports the FIRST state matching each
#      of ten "the game should never be here" predicates (Mario off the world, GES out of range,
#      OperMode/WorldNumber/AreaPointer changed, an out-of-table Enemy_ID -- the H43 JumpEngine
#      doorway --, a non-zero EnemyFrenzyBuffer, an over-filled VRAM buffer, climbing with no vine,
#      a jumped PageLoc) and dumps its path.  Any hit is a new primitive to triage.
set -e
cd "$(dirname "$0")/../.."
CORE=third_party/QuickNES_Core/quicknes_libretro.so
ROM="roms/Super Mario Bros. (W) [!].nes"
IN=data/wr/wr_inputs.bin
S="${SECS:-14400}"
K="--enemycell 0 --xcell 8 --ycell 16 --spdcell 16 --relcell 32"
go() { # go TAG ROOT HORIZON SEED
  systemd-run --user --scope -q -p MemoryMax=1800M --unit "e6-$1" -- \
    ./build/explore "$CORE" "$ROM" "$IN" --root $2 --horizon $3 \
    --max-addr 0x300 --max-weight 20 --prog-fw 1 --anomaly \
    --cells 100000 --rollout 6,50 $K --seed $4 --secs "$S" --report 240 --out runs/E6-vram \
    > "runs/E6-vram/$1.log" 2>&1 &
  echo "launched e6-$1 root=$2"
}
go w12 2483 1290 71     # 1-2: where WarpZoneControl matters; wall clip, warp zone, coins, bricks
go w42 6582  700 72     # 4-2: the densest block/vine/item level on the route
go w11  193  380 73     # 1-1: short, block-dense, and it holds the known wall-entry sites
