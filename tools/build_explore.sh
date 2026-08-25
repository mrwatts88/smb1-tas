#!/bin/sh
# Track E finder.  Separate from build_core.sh / build_oracle.sh on purpose.
#
# Builds to a temp file and renames it into place: a rename is atomic and leaves any RUNNING
# search's mapped inode alone, so a rebuild mid-search neither fails with ETXTBSY nor corrupts
# a job in flight.  Set OUT= to build a second binary alongside the running one.
set -e
cd "$(dirname "$0")/.."
mkdir -p build runs/E3
OUT="${OUT:-build/explore}"
gcc -O2 -march=native -std=gnu11 -I third_party/QuickNES_Core/libretro/libretro-common/include \
    -o "$OUT.tmp$$" src/fastcore/explore.c -ldl
mv -f "$OUT.tmp$$" "$OUT"
echo "built $OUT"
