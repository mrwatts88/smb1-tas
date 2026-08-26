#!/bin/sh
# L4 — 8-4 room 2's exit pipe: 15 priced frames of geometric loss, never searched.
#
# THE SITE (F245, `runs/E9a/loss_map.txt` w84r2).  Room 2's 267 control frames lose 55 off-cap
# frames, 23 of them in one run at **rows 16158-16180, x 2405->2429 (cols 150-151), y 64->100,
# speed +38 -> +23**, with `blocking ahead: (r4,c152 0x10) (r4,c153 0x11) (r5,c152 0x14)
# (r5,c153 0x15)`.  That is the deceleration into the vertical exit pipe: Mario gives up 15
# priced frames of forward motion to arrive on the pipe mouth.  The WR enters at **core frame
# 16182** at x 2436 (page 9, X 132), Y 64, x-speed 19.
#
# WHY IT IS OPEN.  MrWint's `W84Part2VertPipeEntry` proves 40 frames optimal FROM x 2373 (rows
# 16145->16185) and the WR matches it -- but that segment fixes the state at x 2373 by
# construction, which is H39's seam corollary: the approach chooses that state, and no search has
# ever varied it.  This is an ARC problem (a different approach height/subpixel over the c152/153
# blocks), which is why the key carries `--subcell 16 --ysubcell 64`: F245/F247 put these windows
# at 1-2 px and E9b showed a key without a subpixel dimension is below the resolution of the
# question.
#
# THE GOAL, AND WHY IT IS THE RIGHT QUANTITY (doctrine: F230/F237 -- a proxy goal makes fake
# records).  Goal = `GameEngineSubroutine == 3` (pipe entry), baseline **16182** = the WR's own,
# reproduced exactly by the control below.  Monotone with the record because 8-4 is unquantized
# (no flagpole, no framerule) and an area load costs a constant 122 frames from load to control
# with exactly one lag frame at every ITC phase (F264/F265) -- so entering the correct pipe k
# frames earlier starts room 3 k frames earlier and ends the game k frames earlier.
# **"the correct pipe" is the whole caveat:** room 2 also has loop-back pipes, and the control run
# already produced one (`AreaPointer = 229` + a 255 px position jump at frame 16223, x 1536).  So
# EVERY candidate must be core-replayed and DESTINATION-checked (runbook 4.3) before it counts.
#
# THE PAGE-9 CLAUSE (session 22 -- ADDED AFTER IT BIT, F274).  The first full-size `w` run reported
# `GOAL frame=16074 (-108)` and `16070 (-112)` *** AHEAD OF THE WR *** within ten minutes.  Both are
# the room-2 LOOP-BACK pipe: entry at **x 2116 (page 8)**, and the core replay dumps Mario back at
# **x 312**, start of room 2, `AreaPointer` still $65 (`runs/L4-w84r2/s22_nopage/`).  The WR's exit
# pipe is at **x 2436 = page 9, X 132**.  `GameEngineSubroutine == 3` alone fires on ANY pipe.
# Worse than a false positive: ONGOAL (explore.c:454) only ever records a goal that IMPROVES on the
# incumbent, so a 16070 loop-back permanently blinds the run to every real entry (which cannot be
# earlier than ~16150).  The run could no longer answer its own question.
# Fix: the goal pairs are ANDed (explore.c:132), so `--goal-ram 0x0e=3,0x6d=9` requires the pipe
# entry to happen on **page 9**, which the loop-back at page 8 cannot satisfy and the WR's own entry
# does -- the control gate still reproduces 16182.  The destination check stays mandatory anyway:
# page 9 narrows the pipe, it does not identify it.
# CONTROL GATE (green, 2026-08-25, `runs/L4-w84r2/ctrl/`): root 16050, 40 s, 4,000 cells ->
#   `GOAL frame=16182  (baseline 16182, +0)`  -- the seeded WR line reproduces its own entry.
#
# Usage:  [SECS=21600] [CELLS=40000] [MEMMAX=700M] [ONLY="a"] [SKIP="w"] ./runs/L4-w84r2/launch.sh
# A goal under 16182 is a BANKED FRAME and, in 8-4, one frame is the record (F245/H24) -- replay
# it with tools/e3_replay.py, check the destination, then sync in FCEUX + BizHawk (PROCESS).
set -e
cd "$(dirname "$0")/../.."
CORE=third_party/QuickNES_Core/quicknes_libretro.so
ROM="roms/Super Mario Bros. (W) [!].nes"
IN=data/wr/wr_inputs.bin
S="${SECS:-21600}"
C="${CELLS:-40000}"
M="${MEMMAX:-700M}"
K="--enemycell 0 --xcell 2 --ycell 4 --spdcell 4 --relcell 2 --subcell 16 --ysubcell 64"

go() { # go TAG ROOT HORIZON SEED
  case " ${SKIP:-} " in *" $1 "*) return 0 ;; esac
  if [ -n "${ONLY:-}" ]; then case " ${ONLY} " in *" $1 "*) ;; *) return 0 ;; esac; fi
  systemd-run --user --scope -q -p MemoryMax="$M" --unit "l4-$1" -- \
    ./build/explore "$CORE" "$ROM" "$IN" --root $2 --horizon $3 \
    --goal-ram 0x0e=3,0x6d=9 --baseline 16182 --anomaly \
    --cells "$C" --rollout 6,50 $K --seed $4 --secs "$S" --report 300 --out runs/L4-w84r2 \
    > "runs/L4-w84r2/$1.log" 2>&1 &
  echo "launched l4-$1 root=$2 horizon=$3 cells=$C memmax=$M secs=$S"
}
go a 16050 200 91   # the approach: 132 frames to the WR's entry, the arc and its subpixel
go w 15905 350 92   # the whole room from control 15918: lets the approach STATE vary, not just the arc
