#!/bin/sh
# Track E on 8-4.  8-4 is unquantized (H24): ONE frame anywhere in it is the record.
#
# 8-4 is a MAZE implemented by area-change commands in E_CastleArea6 (page 3 col 8 -> $65 p1,
# page 5 col 3 -> $65 p7, page 8 col 5 -> $65 p1, page 9 col 15 -> $65 p12, page 13 col 4 ->
# $65 p1, page 14 col 4 -> $02 p0, page 17 col 15 -> $65 p1).  Most pipes send you BACK to
# page 1.  So "a pipe was entered" is NOT a goal -- the first version of this run reported
# -54 and -102 frames and both were wrong-pipe entries.  The goal below is the DESTINATION:
# GES 7 + AltEntranceControl 2 + the next room's page + X 56, i.e. Mario rising out of the
# correct pipe in the correct room.  Baselines are the WR's own first frame at that signature.
#
#   room1  control 15220 -> dest page  7 at 15818
#   room2  control 15914 -> dest page 12 at 16255
#   room3  control 16351 -> dest page  0 at 16620   (ends in a scroll-gated turnaround)
#   water  control 16716 -> dest page 16 at 17490   (696 frames, never searched by anyone)
set -e
cd "$(dirname "$0")/../.."
CORE=third_party/QuickNES_Core/quicknes_libretro.so
ROM="roms/Super Mario Bros. (W) [!].nes"
IN=data/wr/wr_inputs.bin
run() {  # run TAG ROOT DESTPAGE BASELINE HORIZON PROGX SEED
  systemd-run --user --scope -q -p MemoryMax=1800M --unit "e3w84-$1" -- \
    ./build/explore "$CORE" "$ROM" "$IN" \
      --root $2 --goal-ram 0x0e=7,0x752=2,0x6d=$3,0x86=56 --baseline $4 \
      --horizon $5 --prog-x $6 --prog-fw 4 \
      --cells 100000 --rollout 6,50 --enemycell 16 --seed $7 \
      --secs "${SECS:-10800}" --report 180 --out runs/E3-w84 \
    > "runs/E3-w84/$1.log" 2>&1 &
  echo "launched $1 root=$2 destpage=$3 baseline=$4 -> runs/E3-w84/$1.log"
}
run room3 16351 0  16620 320 3404 11
run water 16716 16 17490 820 1076 22
run room2 15914 12 16255 400 2436 33
run room1 15220 7  15818 660 1137 44
