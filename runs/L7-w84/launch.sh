#!/bin/sh
# L7 — the novelty sweep on 8-4, the one level it was never run on, with the object-slot lens.
#
# TWO gaps, both from docs/open-threads.md:
#   (a) `build/explore --anomaly` (the P3.4 sweep, runs/E6-vram/) covered 1-1, 1-2, 4-1, 4-2, 8-2
#       and 8-3, each rooted at its level start.  **8-4 was never swept, in any of its five
#       sub-areas** — and 8-4 is the only unquantized level, where ONE frame is the record.
#   (b) No sweep ever carried an OBJECT-SLOT lens.  Class 5 only fired on Enemy_ID > $36 (out of
#       the JumpEngine table) over 5 of the 6 slots, so it could never see F258's mechanism, which
#       is $31 (StarFlagObject, <= $36) in a spare slot.  explore.c now has:
#         class 17 "Enemy_ID novel in a live slot"  — calibrated: any id in a slot with
#                   Enemy_Flag != 0 that the WR's own line through this region never parks anywhere.
#         class 18 "StarFlagObject in a slot"       — calibrated BY COUNT: fires only when more
#                   slots hold $31 than the reference line ever holds here (the end-of-level castle
#                   legitimately parks one).  That is F258's 857 frames.
#       Class 5 now covers all six slots ($16-$1b), so anom_5 hits are not comparable with E6's.
#
# The five sub-area roots are the WR's own control frames (GameEngineSubroutine 8) minus ~13, the
# same convention E6 used, read from data/wr/fceux_wr.ram with tools/ram_trace.py:
#   control 15224 (room 1) / 15918 (room 2) / 16355 (room 3) / 16720 (water) / 17590 (Bowser)
#   pipe entries (GES 3/2) 15748 / 16185 / 16550 / 17416; the axe ends the run at 17868.
# The Bowser-room root is the only one whose horizon reaches the default goal (OperMode 2 &&
# World >= 7 = the ending), so that job doubles as an H1 ending-input probe: it prints
# `last_input` against the WR's 17846 and writes runs/L7-w84/best_*.path when it beats it.
#
# Usage:  [SECS=21600] [CELLS=80000] [MEMMAX=1500M] [WAIT=1] [ONLY=r5] ./runs/L7-w84/launch.sh
#   WAIT=1  block until at most WAITN (default 0) `explore` processes are running — the box has
#           15 GB and each job wants ~1.2 GB, so five of them alongside three E7 archives will not
#           fit.  Set WAITN to the number of jobs you are deliberately leaving in flight (e.g.
#           WAITN=1 when this launcher's own r5 is already running).  Polls every 60 s, gives up
#           after 12 h.
#   ONLY="r3 r4"  launch only those (space-separated).  SKIP="r5" launches everything but those —
#           use it when one tag is already in flight, so the queued batch does not relaunch it on
#           top of itself (same log file, same systemd unit name).
# Read the results:  grep ANOMALY runs/L7-w84/*.log   then  tools/e3_replay.py runs/L7-w84/anom_*.path
set -e
cd "$(dirname "$0")/../.."
CORE=third_party/QuickNES_Core/quicknes_libretro.so
ROM="roms/Super Mario Bros. (W) [!].nes"
IN=data/wr/wr_inputs.bin
S="${SECS:-21600}"
C="${CELLS:-80000}"
M="${MEMMAX:-1500M}"
K="--enemycell 0 --xcell 8 --ycell 16 --spdcell 16 --relcell 32"

if [ "${WAIT:-0}" = "1" ]; then
  n=0
  while [ "$(pgrep -x -c explore 2>/dev/null || echo 0)" -gt "${WAITN:-0}" ]; do
    n=$((n+1))
    [ "$n" -gt 720 ] && { echo "WAIT: still busy after 12 h, giving up"; exit 4; }
    sleep 60
  done
  echo "WAIT: <= ${WAITN:-0} explore running, launching at $(date -u +%FT%TZ)"
fi

# SEEDADD added 2026-08-26 (s22) to MATCH launch_mac.sh.  The two launchers for this one job had
# already drifted twice in a single session -- the CELLS 60000/80000 default split, and ONLY/SKIP
# existing here but not there (F281) -- so keeping them feature-identical IS the fix.  SEEDADD offsets
# every seed and renames the tag, so re-running an already-covered root is INDEPENDENT coverage rather
# than a byte-identical duplicate (same binary + same params + same seed = the same rollouts).
go() { # go TAG ROOT HORIZON SEED
  case " ${SKIP:-} " in *" $1 "*) return 0 ;; esac
  if [ -n "${ONLY:-}" ]; then case " ${ONLY} " in *" $1 "*) ;; *) return 0 ;; esac; fi
  TAG="$1"
  SEED=$(( $4 + ${SEEDADD:-0} ))
  if [ "${SEEDADD:-0}" -ne 0 ]; then TAG="$1s${SEEDADD}"; fi
  systemd-run --user --scope -q -p MemoryMax="$M" --unit "l7-$TAG" -- \
    ./build/explore "$CORE" "$ROM" "$IN" --root $2 --horizon $3 \
    --max-addr 0x300 --max-weight 20 --prog-fw 1 --anomaly \
    --cells "$C" --rollout 6,50 $K --seed $SEED --secs "$S" --report 300 --out runs/L7-w84 \
    > "runs/L7-w84/$TAG.log" 2>&1 &
  echo "launched l7-$TAG root=$2 horizon=$3 cells=$C memmax=$M secs=$S seed=$SEED"
}
go r1 15210  800 81   # room 1  — control 15224, pipe 15748; horizon runs into room 2's start
go r2 15905  550 82   # room 2  — control 15918, pipe 16185; L4's 15-frame exit-pipe site (cols 150-152)
go r3 16342  500 83   # room 3  — control 16355, pipe 16550; L3's 38-frame approach + the turnaround
go r4 16707  950 84   # water   — control 16720, side pipe 17416; the 696-frame swim, never searched at all
go r5 17577  400 85   # Bowser  — control 17590, axe 17868; reaches the ending goal (H1/H17 live here)
