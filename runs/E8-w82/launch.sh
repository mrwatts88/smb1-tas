#!/bin/sh
# E8 — 8-2's ending, the last unexamined pocket on the route.
#
# F225: 8-2 has 213 off-cap control frames, the most of any framerule level after 4-2, and they sit
# almost entirely in one place -- dump rows 12275-12457, where Mario spends ~126 frames climbing a
# shaft (x moves 3261 -> 3313, i.e. 52 px, while Y goes 444 -> 368 -> 304 in three alternating
# hops) and then runs off the high platform, accelerating all the way down to the flagpole at
# x 3449.  Nobody in this project has ever searched 8-2, and MrWint solved no segment of it.
# 52 px at the cap is 21 frames, so ~105 of those frames are the climb itself.
#
# Goal: the flagpole grab -- GameEngineSubroutine == 5 (PlayerEndLevel), which the WR reaches at
# core 12472.  For a flag level the level end is grab + T + constants (F27/F32), and T only moves
# every 24 frames, so an earlier grab is an earlier end frame-for-frame.
# **8-2's deficit is 19 (F29), so a grab at core <= 12453 is a framerule = a new record.**
# Prior is poor -- 19 frames is the largest live deficit on the board -- but this is the only
# pocket left that nobody has looked at, and 8-4-style structural surprises live in exactly such
# places.  Verify any hit with the recipe in docs/experiments/P4E-finder.md.
set -e
cd "$(dirname "$0")/../.."
CORE=third_party/QuickNES_Core/quicknes_libretro.so
ROM="roms/Super Mario Bros. (W) [!].nes"
IN=data/wr/wr_inputs.bin
S="${SECS:-21600}"
go() { # go TAG ROOT HORIZON SEED
  systemd-run --user --scope -q -p MemoryMax=2000M --unit "e8-$1" -- \
    ./build/explore "$CORE" "$ROM" "$IN" --root $2 --horizon $3 \
    --goal-ram 0x0e=5 --baseline 12472 --prog-x 3449 --prog-fw 4 \
    --cells 130000 --rollout 5,48 --enemycell 24 --xcell 6 --ycell 12 --spdcell 8 --relcell 16 \
    --seed $4 --secs "$S" --report 300 --out runs/E8-w82 > "runs/E8-w82/$1.log" 2>&1 &
  echo "launched e8-$1 root=$2 horizon=$3"
}
go climb 12240 320 501   # rooted just before the shaft climb
go wide  12100 460 502   # rooted earlier, so the approach to the shaft is free too (H39)
