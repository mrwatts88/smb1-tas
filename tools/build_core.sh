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
# --- MrWint/smb-opt (P1.2-lite): player-physics model + XPos table ---
# Needs a 2018 Rust nightly (rustup, user-level): sh rustup-init.sh -y --no-modify-path --default-toolchain nightly-2018-06-01 --profile minimal
if [ ! -d third_party/smb-opt ]; then
  git clone https://github.com/MrWint/smb-opt.git third_party/smb-opt
  ( cd third_party/smb-opt && git checkout -q daa44287bc9ccab7e85b430e80bf7dff77542542 && git apply ../../tools/smb-opt-modes.patch )
fi
if [ -x "$HOME/.cargo/bin/cargo" ]; then
  ( cd third_party/smb-opt && "$HOME/.cargo/bin/cargo" build --release ) && \
  third_party/smb-opt/target/release/smb-opt xpos-dump data/xpos_table_11.txt && echo "built smb-opt and data/xpos_table_11.txt"
else
  echo "skipping smb-opt (no ~/.cargo/bin/cargo)"
fi
