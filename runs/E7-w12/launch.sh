#!/bin/sh
# E7 — 1-2's endgame, posed as ONE question with no intermediate gate.  THE LIVE RECORD ATTEMPT.
#
# Why this shape.  F236: 1-2's wall clip is a scroll mint -- ScreenLeft freezes at 2563 for ~30
# frames while Mario is ejected +1 px/frame through the wall, and he leaves it at rel 128 instead
# of the 112 cap.  By F229 the warp then arms (ScreenLeft 2816) only at max_x = 2944 instead of
# 2928.  So the clip has TWO costs -- the frames it takes and the lead it mints -- and they trade.
# Every earlier search here goaled on a position or a step and let the scroll fall out however it
# fell out; that is exactly why F144's three clip frames were "refunded".
#
# Goal: the thing itself -- WorldNumber == 3, the world-4 warp actually taken.  Baseline core 3763.
# 1-2's deficit is 8, so **a goal at core <= 3755 IS A NEW RECORD.**  Verify any hit by replaying it
# (tools/e3_replay.py) and then in FCEUX + BizHawk before believing it.
#
# Promise = ScreenLeft (--prog-off -1 with no --prog-x makes prog = x - rel = ScreenLeft), because
# ScreenLeft is the gate, not Mario's x.  After the text object arms the zone, ScrollLock freezes
# ScreenLeft, so every phase-2 cell scores alike and the frame penalty drives toward the pipe.
# --max-addr 0x6d6 --max-weight 0 puts WarpZoneControl in the cell key (so armed and un-armed
# states never merge) without letting it steer the promise.
set -e
cd "$(dirname "$0")/../.."
CORE=third_party/QuickNES_Core/quicknes_libretro.so
ROM="roms/Super Mario Bros. (W) [!].nes"
IN=data/wr/wr_inputs.bin
S="${SECS:-21600}"
go() { # go TAG ROOT SEED RELCELL
  systemd-run --user --scope -q -p MemoryMax=2000M --unit "e7-$1" -- \
    ./build/explore "$CORE" "$ROM" "$IN" --root $2 --horizon 300 \
    --goal-ram 0x75f=3 --baseline 3763 --prog-off -1 --prog-fw 4 \
    --max-addr 0x6d6 --max-weight 0 \
    --cells 130000 --rollout 4,44 --enemycell 0 --xcell 4 --ycell 8 --spdcell 8 --relcell $4 \
    --seed $3 --secs "$S" --report 300 --out runs/E7-w12 > "runs/E7-w12/$1.log" 2>&1 &
  echo "launched e7-$1 root=$2"
}
go pre  3540 401 4      # before the clip: the clip itself and its mint are free to change
go mid  3600 402 2      # after the clip, rel already 128: only the turnaround is free
go early 3400 403 4     # 140 frames before the clip: the APPROACH to the clip is free too
                        # (launched with --horizon 440 --cells 150000 --xcell 6 --ycell 12)
