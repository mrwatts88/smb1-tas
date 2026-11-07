#!/bin/sh
# H35 — 4-2's warp zone: 30 priced frames of loss (F245), 15 frames of slack against the staged
# bound (F89: 461 vs the WR's 476), and NEVER SEARCHED (reopened 2026-11-07).
#
# THE SITE.  The WR runs the roof at Y 32 at full speed, brakes from x ~943, drops through the
# roof gap (cols 60-61) at x 958, then runs back LEFT at cap under the roof and hops into the
# world-8 pipe at x ~810.  F90 proves the return optimal FROM the WR's own drop state; F89 puts all
# 15 slack frames in the last ~100 steps (braking, fall, landing).  So the question is whether a
# DIFFERENT drop state (x / speed / subpixel / height at the gap) makes the whole thing cheaper.
# That is an arc problem, hence the subpixel key (same key as L4).
#
# THE GOAL.  `GameEngineSubroutine == 3` AND `WorldNumber == 7`: a pipe entry that has already
# set world 8.  The world byte identifies the pipe outright (the 6/7 pipes set 5/6), so no
# wrong-pipe trap (F274's lesson).  Monotone with the record: entry -> fixed pipe descent -> 8-1
# load -> card, whose wait absorbs any gain until it crosses the 21-frame rule (F28/F237).
# WR: dump row 7724 = core 7721 (F45: core = row - 3).
#   * goal < 7721  : banked (sub-threshold)
#   * goal <= 7711 : a framerule TOGETHER WITH F88's 3 main-area frames (4-2 deficit 13, F29)
#   * goal <= 7708 : a framerule on its own
# The warp-zone load is a sub-area load (not quantized, F28), so F88's earlier entry shifts this
# room 1:1 — still to be confirmed on the core by splicing, if a hit lands in 7709-7711.
#
# PROMISE (per root).  `a*` roots start on the roof: default "x to the right" is wrong there (the
# pipe is back LEFT of the gap), so  --prog-x 810 scores closeness to the pipe; --max-addr 0xce --max-weight 1 adds Mario's
# Y so dropping through the gap is rewarded.  (Side effect: the log prints `MAX $00ce` lines with
# 8-4/ACE wording — cosmetic, ignore.)  `w*` roots start on the FLOOR at x 24 and must climb to the
# roof first; the Y bonus pulled them into pits (first launch, 2026-11-07, killed after ~2 min), so
# they use the default rightward progress.  Cells keep both phases regardless; this only biases picks.
#
# Usage:  [SECS=21600] [CELLS=120000] [MEMMAX=2000M] [ONLY="a1"] ./runs/H35-w42warp/launch.sh
set -e
cd "$(dirname "$0")/../.."
CORE=third_party/QuickNES_Core/quicknes_libretro.so
ROM="roms/Super Mario Bros. (W) [!].nes"
IN=data/wr/wr_inputs.bin
S="${SECS:-21600}"
C="${CELLS:-120000}"
M="${MEMMAX:-2000M}"
K="--enemycell 0 --xcell 2 --ycell 4 --spdcell 4 --relcell 2 --subcell 16 --ysubcell 64"
P="--prog-x 810 --max-addr 0xce --max-weight 1"

go() { # go TAG ROOT HORIZON SEED PROMISE
  if [ -n "${ONLY:-}" ]; then case " ${ONLY} " in *" $1 "*) ;; *) return 0 ;; esac; fi
  systemd-run --user --scope -q -p MemoryMax="$M" --unit "h35-$1" -- \
    ./build/explore "$CORE" "$ROM" "$IN" --root $2 --horizon $3 \
    --goal-ram 0x0e=3,0x75f=7 --baseline 7721 $5 \
    --cells "$C" --rollout 6,50 $K --seed $4 --secs "$S" --report 300 --out runs/H35-w42warp/$1 \
    > "runs/H35-w42warp/$1.log" 2>&1 &
  echo "launched h35-$1 root=$2 horizon=$3 cells=$C memmax=$M secs=$S"
}
mkdir -p runs/H35-w42warp/a1 runs/H35-w42warp/a2 runs/H35-w42warp/w1 runs/H35-w42warp/w2 runs/H35-w42warp/ctrl
go a1 7602 170 351 "$P"  # the approach: on the roof at x 874, full speed, before the WR brakes
go a2 7602 170 352 "$P"  #   independent seed (convergence check, as L7)
go w1 7246 520 353 ""  # the whole warp zone from control: lets the roof-run state vary too
go w2 7246 520 354 ""  #   independent seed
