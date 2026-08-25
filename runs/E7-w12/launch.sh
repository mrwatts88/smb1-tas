#!/bin/sh
# E7 — 1-2's endgame, posed as ONE question with no intermediate gate.
#
# Why this shape.  F236: 1-2's wall clip is a scroll mint -- ScreenLeft freezes at 2563 for ~30
# frames while Mario is ejected +1 px/frame through the wall, and he leaves it at rel 128 instead
# of the 112 cap.  By F229 the warp then arms (ScreenLeft 2816) only at max_x = 2944 instead of
# 2928.  So the clip has TWO costs -- the frames it takes, and the lead it mints -- and they trade
# against each other.  Every previous search here goaled on a position or a step and let the scroll
# fall out however it fell out; that is exactly why F144's three clip frames were "refunded".
#
# The goal here is the thing itself: WorldNumber == 3, i.e. the world-4 warp pipe actually taken.
# Baseline core 3763 (WR).  1-2's deficit is 8 on the WR's route, so **a goal at core <= 3755 is a
# framerule = a new record**.  Root is core 3540, ~28 frames before the clip, horizon 300.
# No bound, no layers, real emulator: the scroll is optimised jointly with the movement.
set -e
cd "$(dirname "$0")/../.."
CORE=third_party/QuickNES_Core/quicknes_libretro.so
ROM="roms/Super Mario Bros. (W) [!].nes"
IN=data/wr/wr_inputs.bin
S="${SECS:-21600}"
go() { # go TAG ROOT SEED XCELL RELCELL
  systemd-run --user --scope -q -p MemoryMax=2000M --unit "e7-$1" -- \
    ./build/explore "$CORE" "$ROM" "$IN" --root $2 --horizon 300 \
    --goal-ram 0x75f=3 --baseline 3763 --prog-x 2944 --prog-fw 4 \
    --cells 130000 --rollout 4,44 --enemycell 0 --xcell $4 --ycell 8 --spdcell 8 --relcell $5 \
    --seed $3 --secs "$S" --report 300 --out runs/E7-w12 > "runs/E7-w12/$1.log" 2>&1 &
  echo "launched e7-$1 root=$2"
}
go pre  3540 401 4 4      # before the clip: the clip itself is free to change
go mid  3600 402 4 2      # after the clip, rel already 128: only the turnaround is free
