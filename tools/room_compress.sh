#!/bin/sh
# Compress finished layer files of the P2.1b-m3 run with xz -0 (sorted 16-byte records compress ~17x).
# Keeps the newest 2 layers raw (the engine only writes each file once, at the start of its layer).
cd /home/mattwatts/Documents/smb1-tas/runs/P2.1b-model/room_layers || exit 1
while pgrep -f 'bfs11cr data/wr/wr_inputs.bin 1048 0 238' >/dev/null; do
  last=$(ls layer_*.bin 2>/dev/null | sort | tail -n 1 | sed 's/layer_\([0-9]*\)\.bin/\1/')
  for f in $(ls layer_*.bin 2>/dev/null | sort); do
    n=$(echo "$f" | sed 's/layer_\([0-9]*\)\.bin/\1/')
    if [ -n "$last" ] && [ $((10#$n)) -lt $((10#$last - 1)) ]; then xz -0 -T2 "$f"; fi
  done
  sleep 60
done
