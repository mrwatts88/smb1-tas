#!/bin/sh
# Track E: the cheapest 4-2 wrong-warp mint, measured on the real core.
# Goal = the $2f commit (AreaPointer $2f AND AltEntranceControl 1); WR baseline core frame 7218;
# a framerule needs <= 7205.
# --require-ram 0x750=0x2f: once the parser flips the destination the state is dead (the parser
# only moves forward), so those states are never archived -- a very large, sound prune.
# --watch-x 1341,1363: the pipe-entry x window (F228/HandlePipeEntry).  Reports and dumps the
# best screen-lead (rel = x - ScreenLeft) reached inside it; the warp needs rel >= 132 AND
# Player_X_Scroll == 0 on the entry frame (F227/F129).
# Enemy digest off (--enemycell 0): 4-2's enemies only kill, and the core replay adjudicates.
set -e
cd "$(dirname "$0")/../.."
CORE=third_party/QuickNES_Core/quicknes_libretro.so
ROM="roms/Super Mario Bros. (W) [!].nes"
IN=data/e3/w42_top553.bin
run() {  # run TAG ROOTSTEP HORIZON SEED
  systemd-run --user --scope -q -p MemoryMax=2500M --unit "e3w42-$1" -- \
    ./build/explore "$CORE" "$ROM" "$IN" \
      --root $((6582 + $2)) --horizon $3 --seed $4 \
      --goal-ram 0x750=0x2f,0x752=1 --require-ram 0x750=0x2f --baseline 7218 \
      --prog-x 1348 --prog-off 8 --prog-fw 2 --cells 150000 --rollout 6,50 --enemycell 0 \
      --watch-x 1341,1363 \
      --secs "${SECS:-3600}" --report 180 --out runs/E3-w42 \
    > "runs/E3-w42/$1.log" 2>&1 &
  echo "launched $1 (root step $2, horizon $3, seed $4) -> runs/E3-w42/$1.log"
}
run r200 200 470 404
run r380 380 290 505
run r460 460 210 606
