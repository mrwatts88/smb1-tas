#!/bin/sh
# Track E finder.  Separate from build_core.sh / build_oracle.sh on purpose.
set -e
cd "$(dirname "$0")/.."
mkdir -p build runs/E3
gcc -O2 -march=native -std=gnu11 -I third_party/QuickNES_Core/libretro/libretro-common/include \
    -o build/explore src/fastcore/explore.c -ldl
echo "built build/explore"
