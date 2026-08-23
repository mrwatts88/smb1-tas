#!/bin/sh
# Portable search watchdog (Linux + macOS). Generalises runs/P2.3c-2c/watchdog_d149.sh.
#
# Kills the watched search when a layer's frontier exceeds MAXREC records, or when the
# filesystem holding the layer directory drops below MINFREE GB. Appends a `watchdog:` line
# to the log either way, so a later session can tell a watchdog kill from a real verdict.
#
# usage: tools/watchdog.sh PID LOG MAXREC MINFREE_GB [DIR]
#   PID         search process to watch
#   LOG         search log; scanned for `unique <n>` and appended to
#   MAXREC      kill if any layer reports more than this many unique records
#   MINFREE_GB  kill if DIR's filesystem has less than this many GB free
#   DIR         filesystem to check (default: the log's directory)
set -u
PID=$1; LOG=$2; MAXREC=$3; MINFREE=$4; DIR=${5:-$(dirname "$2")}

# `df -k` is POSIX and puts Available in field 4 on both GNU coreutils and macOS.
free_gb() { df -k "$1" | tail -1 | awk '{ print int($4 / 1048576) }'; }

while kill -0 "$PID" 2>/dev/null; do
  sleep 30
  BIG=$(grep -o 'unique [0-9]*' "$LOG" | awk -v m="$MAXREC" '{ if ($2 > m) print $2 }' | head -1)
  FREE=$(free_gb "$DIR")
  if [ -n "$BIG" ] || [ "$FREE" -lt "$MINFREE" ]; then
    kill "$PID"
    echo "watchdog: killed (frontier ${BIG:-ok}, free ${FREE}G, min ${MINFREE}G)" >> "$LOG"
    exit 0
  fi
done
echo "watchdog: process ended on its own" >> "$LOG"
