#!/bin/sh
# P2.1b-m3 run 4: resume the whole-room search (relaxed model + goombas, deadline 238) from a layer file with the
# external-memory engine (parents streamed from layer_NNN.bin, bounded per-thread accumulators spilled to sorted runs,
# k-way merge into the next layer file). Launch under a cgroup hard cap so an overrun kills only the search:
#   nohup systemd-run --user --scope -p MemoryMax=10G -p MemorySwapMax=512M --quiet sh runs/P2.1b-model/room_run_resume.sh START_LAYER >/dev/null 2>&1 &
# START_LAYER's raw layer file must exist (xz -dc runs/P2.1b-model/room_layers/layer_NNN.bin.xz > .../layer_NNN.bin).
# Log: runs/P2.1b-model/room_compact_d238_r${START}.log (+ .time). Restart runs/P2.1b-model/room_compress.sh alongside.
cd /home/mattwatts/Documents/smb1-tas
START=${1:?start layer}
exec nice -n 10 /usr/bin/time -v third_party/smb-opt/target/release/smb-opt bfs11cr data/wr/wr_inputs.bin 1048 0 238 --goombas --threads 12 \
  --layer-dir runs/P2.1b-model/room_layers --resume "$START" --acc-mb 256 \
  > "runs/P2.1b-model/room_compact_d238_r${START}.log" 2> "runs/P2.1b-model/room_compact_d238_r${START}.time"
