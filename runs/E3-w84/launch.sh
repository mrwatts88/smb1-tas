#!/bin/sh
# Track E on 8-4.  8-4 is unquantized (H24): ONE frame anywhere in it is the record.
#
# 8-4 is a MAZE built from area-change commands in E_CastleArea6 (F230): most pipes send you back
# to page 1, and a pipe's destination is whichever command the parser read last -- read at the
# LOAD, 48 frames after entry, not at entry.  So "GES == 3" (a pipe was entered) is NOT a goal:
# the first version of this run reported -54 and -102 frames and both were wrong-pipe entries.
# The goal below is the DESTINATION: GES 7 + AltEntranceControl 2 + the next room's page + X 56.
#
#   room1  control 15220 -> dest page  7 at 15818   CLOSED (F231: a full lap of a looping
#                                                   corridor, no turnaround, pure running at cap)
#   room2  control 15914 -> dest page 12 at 16255
#   room3  control 16351 -> dest page  0 at 16620   (scroll-gated turnaround, x 3456 -> 3404)
#   water  control 16716 -> dest page 16 at 17490   (696 frames, never searched by anyone)
#   bowser control 17586 -> the axe                 (objective is the LAST INPUT, F17/F223:
#                                                    incumbent 17846, null-coast probe past x 4600)
#
# Cell keys are deliberately COARSE for the room searches (--enemycell 0 --xcell 8 --ycell 16
# --spdcell 8 --relcell 16): the first, finer pass evicted 400k states against a 100k archive.
set -e
cd "$(dirname "$0")/../.."
CORE=third_party/QuickNES_Core/quicknes_libretro.so
ROM="roms/Super Mario Bros. (W) [!].nes"
IN=data/wr/wr_inputs.bin
S="${SECS:-10800}"
COARSE="--enemycell 0 --xcell 8 --ycell 16 --spdcell 8 --relcell 16"

systemd-run --user --scope -q -p MemoryMax=2200M --unit e3w84-room3 -- \
  ./build/explore "$CORE" "$ROM" "$IN" --root 16351 \
  --goal-ram 0x0e=7,0x752=2,0x6d=0,0x86=56 --baseline 16620 --horizon 320 --prog-x 3404 --prog-fw 4 \
  --cells 150000 --rollout 6,50 $COARSE --seed 111 --secs "$S" --report 180 --out runs/E3-w84 \
  > runs/E3-w84/room3.log 2>&1 &

systemd-run --user --scope -q -p MemoryMax=2200M --unit e3w84-room2 -- \
  ./build/explore "$CORE" "$ROM" "$IN" --root 15914 \
  --goal-ram 0x0e=7,0x752=2,0x6d=12,0x86=56 --baseline 16255 --horizon 400 --prog-x 2436 --prog-fw 4 \
  --cells 150000 --rollout 6,50 $COARSE --seed 222 --secs "$S" --report 180 --out runs/E3-w84 \
  > runs/E3-w84/room2.log 2>&1 &

systemd-run --user --scope -q -p MemoryMax=1800M --unit e3w84-water -- \
  ./build/explore "$CORE" "$ROM" "$IN" --root 16716 \
  --goal-ram 0x0e=7,0x752=2,0x6d=16,0x86=56 --baseline 17490 --horizon 820 --prog-x 1076 --prog-fw 4 \
  --cells 100000 --rollout 6,50 --enemycell 16 --seed 22 --secs "$S" --report 180 --out runs/E3-w84 \
  > runs/E3-w84/water.log 2>&1 &

systemd-run --user --scope -q -p MemoryMax=1800M --unit e3w84-bowser -- \
  ./build/explore "$CORE" "$ROM" "$IN" --root 17586 --horizon 340 \
  --probe-x 4600 --null-max 220 --coast 300 --prog-x 4805 --prog-fw 4 \
  --cells 100000 --rollout 6,50 --enemycell 16 --seed 55 --secs "$S" --report 180 --out runs/E3-w84 \
  > runs/E3-w84/bowser.log 2>&1 &

echo "launched room3 room2 water bowser -> runs/E3-w84/*.log"
