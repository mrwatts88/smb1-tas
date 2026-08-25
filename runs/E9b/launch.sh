#!/bin/sh
# E9b part 1 — 8-2's columns 201-212 (H48/F245), the largest single geometric loss on the route.
#
# WHY THIS REPLACES runs/E8-w82/launch.sh's `climb`:
#   F245 prices this site at **114 frames** (183 frames for 173 px against a 69-frame bound) and
#   shows the question is a 1-2 PIXEL one: the wall at cols 206-207 clears iff Player_Y_Position
#   <= 55 while x is in [3283, 3314], the WR's own full-speed arc rises 42 px in 25 px of travel,
#   so the jump must be issued at x <= 3259 and he lands on the pillar at x 3258 (first issuable
#   frame x ~ 3260).  The e8 `climb` run keys cells at --xcell 6 --ycell 12 --spdcell 8 with NO
#   subpixel dimension, so a 1-2 px landing question is BELOW ITS RESOLUTION -- it ran 6,900 s
#   with goals=1 and best = the control 12953.  Same defect the Mac session found for 1-2, which
#   is why e7 was relaunched with --subcell.
#
# Goal is unchanged and is the quantity the record is measured in (F230/F237):
#   StarFlagTaskControl ($0746) == 5, baseline core 12952.  A goal at core <= 12931 is one full
#   framerule = a new record.  Anything below 12952 is a banked frame.  Verify EVERY candidate
#   with the recipe in docs/experiments/P4E-finder.md before believing it.
#
# MEMORY: never start a search without a cgroup cap (docs/search-runbook.md §1).  The box is 15 GB
# and each explore archive at 130-200k cells runs 1.7-2.5 GB RSS -- check `free -g` and do not
# start these until the e7/e8 jobs have exited.
set -e
cd "$(dirname "$0")/../.."
CORE=third_party/QuickNES_Core/quicknes_libretro.so
ROM="roms/Super Mario Bros. (W) [!].nes"
IN=data/wr/wr_inputs.bin
S="${SECS:-21600}"
go() { # go TAG ROOT HORIZON SEED SUBCELL YSUBCELL
  systemd-run --user --scope -q -p MemoryMax=2200M --unit "e9b-$1" -- \
    ./build/explore "$CORE" "$ROM" "$IN" --root $2 --horizon $3 \
    --goal-ram 0x746=5 --baseline 12952 --prog-x 3449 --prog-fw 4 \
    --cells 180000 --rollout 4,44 --enemycell 24 --xcell 2 --ycell 4 --spdcell 4 --relcell 8 \
    --subcell $5 --ysubcell $6 \
    --seed $4 --secs "$S" --report 300 --out runs/E9b > "runs/E9b/$1.log" 2>&1 &
  echo "launched e9b-$1 root=$2 horizon=$3 subcell=$5 ysubcell=$6"
}
# root 12157 = core frame for dump row 12160, three frames before the approach jump leaves the
# floor at x 3161 (dump 12252 is the jump frame; the run-up from x 3118 is inside the horizon).
# The whole point is that the APPROACH ARC is what decides the pillar landing pixel, so the root
# must be before it -- e8's 12240 root pre-commits most of the run-up.
go arc16  12157 820 801 16 64
go arc32  12157 820 802 32 64
