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
# Goal: **StarFlagTaskControl == 5**, which IS the area change (F27), at WR core **12952**.
# NOT the grab, and not GES == 5.  The first version of this run used GES == 5 and reported a goal
# 51 frames early; replaying it showed the level ending **126 frames LATE**, because that path
# grabs the pole high and takes a normal slide (GES 4 for 21 frames, then StarFlagTaskControl 2
# only 91 frames later) while the WR's flag glitch goes straight to task 2 in one frame.  Same
# lesson as F230: goal the thing, not a proxy that is cheaper to satisfy.
# The area change is framerule-quantized, so the goal frame can only be 12952 or 12952-21:
# **a goal at core <= 12931 is one full framerule = a new record.**
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
    --goal-ram 0x746=5 --baseline 12952 --prog-x 3449 --prog-fw 4 \
    --cells 130000 --rollout 5,48 --enemycell 24 --xcell 6 --ycell 12 --spdcell 8 --relcell 16 \
    --seed $4 --secs "$S" --report 300 --out runs/E8-w82 > "runs/E8-w82/$1.log" 2>&1 &
  echo "launched e8-$1 root=$2 horizon=$3"
}
go climb 12240 800 501   # rooted just before the shaft climb
go wide  12100 940 502   # rooted earlier, so the approach to the shaft is free too (H39)
