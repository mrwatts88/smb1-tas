#!/bin/sh
# L7 on the Mac (F248): the 8-4 novelty sweep with the object-slot lens, r1-r4.
#
# Why the Mac: `explore` runs natively there (byte-identical, ~3x faster), and the Linux box is
# reserved for L3 (8-4 room 3's approach), which needs the machine to itself.  r5 (Bowser room)
# is already running on Linux and is NOT repeated here.
#
# Track E has no dependency on third_party/smb-opt, so the stale-engine guard does not apply.
# REBUILD FIRST -- this unit changed src/fastcore/explore.c (classes 17/18, class 5 widened to six
# slots), so a Mac binary built before 2026-08-25 cannot see the object-slot lens at all:
#   cd ~/code/smb && git pull
#   clang -O2 -std=gnu11 -I third_party/QuickNES_Core/libretro/libretro-common/include \
#         -o build/explore.tmp src/fastcore/explore.c && mv -f build/explore.tmp build/explore
# CONTROL GATE after any rebuild (cite it): the 13,000-frame RAM trace must match the Linux box's --
#   ./build/harness .../quicknes_libretro.dylib ROM data/wr/wr_inputs.bin --frames 13000 \
#       --input-skip 2 --ram /tmp/mac.ram && shasum -a 256 /tmp/mac.ram
#
# MEMORY: macOS has no cgroups.  `explore`'s archive is a fixed-capacity table (--cells) with
# eviction, so RSS is flat; --cells 60000 is ~0.77 GB each, ~3.1 GB for the four.  The RSS
# watchdog below is the belt-and-braces version of the standing never-uncapped rule.
#
# Usage: [SECS=21600] [CELLS=60000] [WAIT=1] [WAITN=0] ./runs/L7-w84/launch_mac.sh
#   WAIT=1 blocks until at most WAITN explore processes remain (use it to queue behind E9b).
# Read the results:  grep ANOMALY runs/L7-w84/*.log
set -e
cd "$(dirname "$0")/../.."
CORE=third_party/QuickNES_Core/quicknes_libretro.dylib
ROM="roms/Super Mario Bros. (W) [!].nes"
IN=data/wr/wr_inputs.bin
S="${SECS:-21600}"
C="${CELLS:-60000}"
K="--enemycell 0 --xcell 8 --ycell 16 --spdcell 16 --relcell 32"

if [ "${WAIT:-0}" = "1" ]; then
  n=0
  while [ "$(pgrep -x -c explore 2>/dev/null || echo 0)" -gt "${WAITN:-0}" ]; do
    n=$((n+1))
    [ "$n" -gt 720 ] && { echo "WAIT: still busy after 12 h, giving up"; exit 4; }
    sleep 60
  done
  echo "WAIT: launching at $(date -u +%FT%TZ)"
fi

go() { # go TAG ROOT HORIZON SEED
  ./build/explore "$CORE" "$ROM" "$IN" --root $2 --horizon $3 \
    --max-addr 0x300 --max-weight 20 --prog-fw 1 --anomaly \
    --cells "$C" --rollout 6,50 $K --seed $4 --secs "$S" --report 300 --out runs/L7-w84 \
    > "runs/L7-w84/$1.log" 2>&1 &
  echo "launched l7-$1 pid $! root=$2 horizon=$3 cells=$C"
}
go r1 15210  800 81   # room 1  — control 15224, pipe 15748
go r2 15905  550 82   # room 2  — control 15918, pipe 16185 (L4's site)
go r3 16342  500 83   # room 3  — control 16355, pipe 16550 (L3's site)
go r4 16707  950 84   # water   — control 16720, side pipe 17416; never searched at all
# RSS watchdog: kill any explore over 1.5 GB, check every 60 s
( while true; do
    for p in $(pgrep -x explore); do
      rss=$(ps -o rss= -p "$p" 2>/dev/null | tr -d ' ')
      [ -n "$rss" ] && [ "$rss" -gt 1572864 ] && kill "$p" && echo "watchdog killed $p rss=$rss" >> runs/L7-w84/watchdog.log
    done
    sleep 60
  done ) > /dev/null 2>&1 &
echo "watchdog pid $!"
