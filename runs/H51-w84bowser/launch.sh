#!/bin/sh
# H51 — the 8-4 Bowser room, keyed on Bowser, scored on the LAST INPUT (WR 17846).
#
# Why: F296/F299. The WR's ending threads Bowser's hitbox with < 0.5 px either side (1/8 px back
# -> clipped by his back edge at 17844; 1 px forward -> lands on him at 17828; the flame is ~200 px
# away). So an earlier last input needs a different Mario-vs-Bowser timing, not more speed.
# Earlier Bowser-room runs (L7 r5: --enemycell 0 --xcell 8; E3-w84 bowser: --enemycell 16, 9 min)
# could not tell those timings apart.
#
# Key: Mario x/2 px, y/4, speed/4, real x-subpixel $0400/16 and y-subpixel $0416/64 (F297 fix),
# Bowser's x/4 (--enemycell 4, all live slots) and Bowser's y/2 (--keyaddr 0xd0/2, slot 1 — the
# trace shows Bowser in slot 1, flame in slot 0). b3/b4 add the x speed fraction $0705/32.
# No --goal-ram: the default goal is the ending (OperMode 2 && World >= 7), every goal is
# tail-trimmed, and the run reports last_input against 17846.
#
# Control (2026-11-07, 40 s, seed 1): seeded WR line 282 cells, GOAL last_input=17846 (+0).
# Usage: [SECS=28800] [CELLS=120000] [MEMMAX=2000M] [ONLY="b1 b2"] ./runs/H51-w84bowser/launch.sh
# Read:  grep "GOAL\|done:" runs/H51-w84bowser/*.log ; a last_input <= 17845 is a new record
#        (then: replay the path with tools/e3_replay.py, then two-emulator verification).
set -e
cd "$(dirname "$0")/../.."
CORE=third_party/QuickNES_Core/quicknes_libretro.so
ROM="roms/Super Mario Bros. (W) [!].nes"
IN=data/wr/wr_inputs.bin
S="${SECS:-28800}"
C="${CELLS:-120000}"
M="${MEMMAX:-2000M}"
K="--enemycell 4 --xcell 2 --ycell 4 --spdcell 4 --relcell 2 --subcell 16 --ysubcell 64 --keyaddr 0xd0/2"
go() { # go TAG SEED EXTRA
  if [ -n "${ONLY:-}" ]; then case " ${ONLY} " in *" $1 "*) ;; *) return 0 ;; esac; fi
  systemd-run --user --scope -q -p MemoryMax="$M" --unit "h51-$1" -- \
    ./build/explore "$CORE" "$ROM" "$IN" --root 17577 --horizon 300 \
    --cells "$C" --rollout 6,50 $K $3 --seed $2 --secs "$S" --report 300 --out "runs/H51-w84bowser/$1" \
    > "runs/H51-w84bowser/$1.log" 2>&1 &
  echo "launched h51-$1 seed=$2 extra='$3' secs=$S cells=$C memmax=$M"
}
go b1 511 ""
go b2 512 ""
go b3 513 "--frccell 32"
go b4 514 "--frccell 32"
