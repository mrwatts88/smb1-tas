#!/bin/sh
# Clone + build the QuickNES libretro core and the headless harness (P1.1). Idempotent.
#   third_party/QuickNES_Core/quicknes_libretro.so   (gitignored)
#   build/harness                                     (gitignored)
set -e
cd "$(dirname "$0")/.."
mkdir -p third_party build
if [ ! -d third_party/QuickNES_Core ]; then
  git clone --depth 1 https://github.com/libretro/QuickNES_Core.git third_party/QuickNES_Core
fi
( cd third_party/QuickNES_Core && git rev-parse HEAD && make -j"$(nproc)" )
gcc -O2 -Wall -o build/harness src/fastcore/harness.c -I third_party/QuickNES_Core/libretro/libretro-common/include -ldl
echo "built build/harness and third_party/QuickNES_Core/quicknes_libretro.so"
