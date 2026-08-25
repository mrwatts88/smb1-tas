#!/bin/sh
# P3.2 band sweep.  Usage: launch_sweep.sh TAG AT_FRAME ADDR_LO ADDR_HI
# Single-threaded and nice'd on purpose: a second session is running Track A on this box.
set -e
cd "$(dirname "$0")/../.."
TAG="$1"; AT="$2"; LO="$3"; HI="$4"
exec ./build/ram_oracle third_party/QuickNES_Core/quicknes_libretro.so \
    "roms/Super Mario Bros. (W) [!].nes" data/wr/wr_inputs.bin \
    --at "$AT" --input-skip 2 --addr-lo "$LO" --addr-hi "$HI" --values all \
    --out "runs/P3.2/${TAG}.csv"
