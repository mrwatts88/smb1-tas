#!/bin/sh
# Build the P3.2 RAM oracle (Track B).  Deliberately separate from tools/build_core.sh so that
# a second session working Track B never edits a file the Track A session may also be editing.
# Requires tools/build_core.sh to have been run once (it clones + builds QuickNES_Core).
set -e
cd "$(dirname "$0")/.."
[ -f third_party/QuickNES_Core/quicknes_libretro.so ] || { echo "run tools/build_core.sh first"; exit 1; }
gcc -O2 -Wall -o build/ram_oracle src/fastcore/ram_oracle.c \
    -I third_party/QuickNES_Core/libretro/libretro-common/include -ldl
echo "built build/ram_oracle"
