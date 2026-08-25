#!/bin/sh
# E7 — 1-2's endgame, posed as ONE question with no intermediate gate.  THE LIVE RECORD ATTEMPT.
#
# The target, worked out by hand (P4E-finder.md "E7 - what 1-2's endgame is actually worth"):
# after the wall clip the WR is at rel 128 instead of the 112 cap, because the clip freezes the
# screen (F236) while Mario is ejected at speed 0.  By F229 the warp then arms only at
# max_x = 2816 + rel = 2944 instead of 2928.  Shedding the lead afterwards costs more than it
# saves (253 px of ScreenLeft would cost 422 px of travel below rel 112).  So the ONE lever is a
# **speed-preserving walk-through** (F80/H33) instead of the speed-killing ejection: it mints
# nothing and takes fewer frames -- worth ~13 + (clip frames saved) against a deficit of 8.
# The WR itself proves the primitive works at full speed: in 4-2 it walks through solid row 10
# from col 33 to col 49 at Y 176 with x-speed pinned at 40 (dump rows 6844-6944).
#
# Goal: the thing itself -- WorldNumber == 3, the world-4 warp actually taken.  Baseline core 3763.
# **A goal at core <= 3755 IS A NEW RECORD** (1-2's deficit is 8).  Verify with the recipe in
# docs/experiments/P4E-finder.md before believing anything.
#
# CELL KEY (this is the part that matters, and the first version got it wrong).  Promise =
# ScreenLeft (--prog-off -1, no --prog-x), because ScreenLeft is the gate, not Mario's x.  And the
# key now carries **--subcell**, the horizontal subpixel: clip windows are 1-2 px and
# subpixel-phase dependent (F93's foot entry drifts +0.95 px/frame; F119's legal band is 6 px), and
# F127 -- the one bucketed beam that ever worked on 4-2 -- bucketed on subpixel.  Without it the
# archive merges exactly the states a walk-through depends on and keeps only the earliest arrival.
# x/y cells are tightened to 2/4 for the same reason.  Diagnosis relayed from the Mac session.
set -e
cd "$(dirname "$0")/../.."
CORE=third_party/QuickNES_Core/quicknes_libretro.so
ROM="roms/Super Mario Bros. (W) [!].nes"
IN=data/wr/wr_inputs.bin
S="${SECS:-21600}"
go() { # go TAG ROOT HORIZON SEED SUBCELL
  systemd-run --user --scope -q -p MemoryMax=3200M --unit "e7-$1" -- \
    ./build/explore "$CORE" "$ROM" "$IN" --root $2 --horizon $3 \
    --goal-ram 0x75f=3 --baseline 3763 --prog-off -1 --prog-fw 4 \
    --max-addr 0x6d6 --max-weight 0 \
    --cells 200000 --rollout 4,44 --enemycell 0 \
    --xcell 2 --ycell 4 --spdcell 4 --relcell 2 --subcell $5 --ysubcell 64 \
    --seed $4 --secs "$S" --report 300 --out runs/E7-w12 > "runs/E7-w12/$1.log" 2>&1 &
  echo "launched e7-$1 root=$2 horizon=$3 subcell=$5"
}
go sub16 3540 300 601 16    # rooted just before the clip, subpixel bucketed to 16
go sub32 3480 360 602 32    # rooted earlier (approach free), coarser subpixel for reach
go body 2900 880 701 32   # rooted at core 2900, BEFORE the known-available frame at step 487
                          # (x 1183, mid-jump over the col-80..82 pit at x-speed 38 not 40).
                          # The endgame roots at 3480/3540 sit past it, so no other run can see it.
                          # Launched with --cells 150000 --xcell 4 --ycell 8 --spdcell 4 --relcell 4
