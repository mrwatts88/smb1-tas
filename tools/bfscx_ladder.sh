#!/bin/sh
# P2.3c-2c: run one `bfscx` segment search per deadline, tight first, until a goal is found (a position-goal BFS only
# stays small when the deadline is near the segment optimum). Each attempt runs under a cgroup cap with a frontier
# watchdog (killed if a layer exceeds MAXREC records); the log of each attempt is LOGBASE_dD.log.
#   tools/bfscx_ladder.sh LOGBASE D0 STEP DMAX MAXREC LAYERDIR -- smb-opt bfscx args without MAX_STEPS
# (args: CASE INPUTS FIRST PREFIX then options; MAX_STEPS is inserted after PREFIX). Absolute paths only.
set -u
LOGBASE=$1; D=$2; STEP=$3; DMAX=$4; MAXREC=$5; LAYERDIR=$6; shift 7
CASE=$1; INPUTS=$2; FIRST=$3; PREFIX=$4; shift 4
BIN=/home/mattwatts/Documents/smb1-tas/third_party/smb-opt/target/release/smb-opt
while [ "$D" -le "$DMAX" ]; do
  LOG="${LOGBASE}_d${D}.log"
  rm -rf "$LAYERDIR"
  systemd-run --user --scope -p MemoryMax=2G -p MemorySwapMax=0 --quiet nice -n 10 "$BIN" bfscx "$CASE" "$INPUTS" "$FIRST" "$PREFIX" "$D" "$@" --layer-dir "$LAYERDIR" > "$LOG" 2>&1 &
  PID=$!
  while kill -0 "$PID" 2>/dev/null; do
    sleep 3
    BIG=$(grep -o 'unique [0-9]*' "$LOG" | awk -v m="$MAXREC" '{ if ($2 > m) print $2 }' | head -1)
    if [ -n "$BIG" ]; then pkill -P "$PID" 2>/dev/null; kill "$PID" 2>/dev/null; echo "deadline $D: frontier $BIG > $MAXREC records, killed" | tee -a "$LOG"; break; fi
  done
  wait "$PID" 2>/dev/null
  if grep -q 'goal reached' "$LOG"; then echo "deadline $D: GOAL — $(grep 'earliest goal' "$LOG" | cut -c1-60)"; exit 0; fi
  if grep -q 'no live states' "$LOG"; then echo "deadline $D: no path (last layer $(grep -c '^layer' "$LOG"))"; else echo "deadline $D: ended without verdict (see $LOG)"; exit 1; fi
  D=$((D + STEP))
done
echo "no goal up to deadline $DMAX"; exit 1
