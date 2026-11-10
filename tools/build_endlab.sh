#!/bin/sh
# Build src/fastcore/endlab.c (N1: exhaustive jump-timing search of the 8-4 final room).
# Needs the QuickNES libretro core (tools/build_core.sh on Linux; on macOS:
#   git clone https://github.com/libretro/QuickNES_Core.git third_party/QuickNES_Core
#   git -C third_party/QuickNES_Core checkout 26bb785c9deddb66a17717b21bb4e328f03ade32
#   make -C third_party/QuickNES_Core platform=osx -j12        -> quicknes_libretro.dylib)
# Portable C, no smb-opt dependency (F248), so it builds natively on both machines.
set -e
cd "$(dirname "$0")/.."
mkdir -p build
INC=third_party/QuickNES_Core/libretro/libretro-common/include
[ -d "$INC" ] || { echo "QuickNES_Core missing: see the header of this script"; exit 1; }
case "$(uname -s)" in
  Darwin) cc -O2 -Wall -o build/endlab src/fastcore/endlab.c -I "$INC" ;;
  *)      gcc -O2 -Wall -o build/endlab src/fastcore/endlab.c -I "$INC" -ldl ;;
esac
echo "built build/endlab"
