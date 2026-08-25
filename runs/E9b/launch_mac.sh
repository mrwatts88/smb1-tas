#!/bin/sh
# E9b part 1 on the Mac (F248): 8-2's cols 201-212, the H48/F247 flag-glitch window.
#
# Track E has NO dependency on third_party/smb-opt or tools/smb-opt-modes.patch, so PROCESS's
# stale-engine guard (tools/mac_run.sh, exit 3) does not apply and the container is not needed:
# build/explore is one portable C file over the libretro core.  Build on the Mac with
#   cd third_party/QuickNES_Core && make platform=osx -j8        # -> quicknes_libretro.dylib
#   clang -O2 -std=gnu11 -I third_party/QuickNES_Core/libretro/libretro-common/include \
#         -o build/explore src/fastcore/explore.c
# CONTROL GATE (run it after every rebuild, and cite it): the 13,000-frame RAM trace of the WR
# inputs must be byte-identical to the Linux box's --
#   ./build/harness .../quicknes_libretro.dylib ROM data/wr/wr_inputs.bin --frames 13000 \
#       --input-skip 2 --ram /tmp/mac.ram   &&  shasum -a 256 /tmp/mac.ram
#   expected 53590a3c94ef0e024c605239a65b7aa6...  (Linux: sha256sum, same prefix)
#
# MEMORY: macOS has no cgroups, so there is no systemd-run MemoryMax here.  `explore` is safe to
# run without one because its archive is a FIXED-CAPACITY table (--cells) with eviction, not a
# growing frontier -- the Linux runs sit at a flat RSS all the way through.  The watchdog below
# is the belt-and-braces version of the standing rule; it kills anything over 3 GB RSS.
set -e
cd "$(dirname "$0")/../.."
CORE=third_party/QuickNES_Core/quicknes_libretro.dylib
ROM="roms/Super Mario Bros. (W) [!].nes"
IN=data/wr/wr_inputs.bin
S="${SECS:-21600}"
go() { # go TAG ROOT HORIZON SEED SUBCELL YSUBCELL
  ./build/explore "$CORE" "$ROM" "$IN" --root $2 --horizon $3 \
    --goal-ram 0x746=5 --baseline 12952 --prog-x 3449 --prog-fw 4 \
    --cells 150000 --rollout 4,44 --enemycell 24 --xcell 2 --ycell 4 --spdcell 4 --relcell 8 \
    --subcell $5 --ysubcell $6 \
    --seed $4 --secs "$S" --report 300 --out runs/E9b > "runs/E9b/$1.log" 2>&1 &
  echo "launched e9b-$1 pid $! root=$2 horizon=$3 subcell=$5 ysubcell=$6"
}
go arc16 12157 820 801 16 64
go arc32 12157 820 802 32 64
# RSS watchdog: kill any explore over 3 GB, check every 60 s
( while true; do
    for p in $(pgrep -x explore); do
      rss=$(ps -o rss= -p "$p" 2>/dev/null | tr -d ' ')
      [ -n "$rss" ] && [ "$rss" -gt 3145728 ] && kill "$p" && echo "watchdog killed $p rss=$rss" >> runs/E9b/watchdog.log
    done
    sleep 60
  done ) > /dev/null 2>&1 &
echo "watchdog pid $!"
