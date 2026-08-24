#!/bin/sh
# Keep only the last KEEP layer_NNN.bin files (plus the tiny early ones <= LOWKEEP) in a bfscx layer dir, so a
# DRY-verdict search fits on a small disk. Safe: only deletes layers >= 4 behind the newest (the engine reads
# layer_{H-1} to build layer_H). NOT for a run whose goal path must be reconstructed. Exits when PID dies.
# usage: tools/layer_pruner.sh PID DIR [KEEP=4] [LOWKEEP=19]
set -u
PID=$1; DIR=$2; KEEP=${3:-4}; LOWKEEP=${4:-19}
while kill -0 "$PID" 2>/dev/null; do
  sleep 20
  H=$(ls "$DIR"/layer_*.bin 2>/dev/null | sed 's/.*layer_0*\([0-9]*\)\.bin/\1/' | sort -n | tail -1)
  [ -n "$H" ] || continue
  CUT=$((H - KEEP))
  K=$((LOWKEEP + 1))
  while [ "$K" -le "$CUT" ]; do
    F=$(printf "%s/layer_%03d.bin" "$DIR" "$K")
    [ -f "$F" ] && rm -f "$F"
    K=$((K + 1))
  done
done
