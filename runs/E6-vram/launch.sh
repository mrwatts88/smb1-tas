#!/bin/sh
# E6 — machine-check F221: how high can VRAM_Buffer1_Offset ($0300) actually go?
#
# Why it matters: `VRAM_Buffer1` is 64 bytes at $0301 but the store is 8-bit indexed, so a large
# enough offset reaches `Block_Orig_YPos` $03e4 / `Block_BBuf_Low` $03e6, which redirects a deferred
# block write anywhere in $0500-$06FE -- including **$06D6 WarpZoneControl**.  A WarpZoneControl
# write in 1-2 sends Mario from 1-2 straight to world 8, skipping 4-1 and 4-2: ~3,957 frames.
# Reaching $03e6 needs offset **227**.  F221 argues the ceiling is ~40-70 by enumerating the
# callers of `MoveVOffset` (+10 per block-metatile write: one head bump per frame, the self-gated
# `BlockObjMT_Updater`, bridge collapse) and observes a max of **67** over the WR's 18,268 frames.
# That is a hand-count against a movie that was not trying.  This measures it.
#
# The finder maximises $0300 directly: the byte is in the cell key (so every distinct value keeps
# its own cells), in the promise, and every new high dumps its path to runs/E6-vram/max_300_N.path.
set -e
cd "$(dirname "$0")/../.."
CORE=third_party/QuickNES_Core/quicknes_libretro.so
ROM="roms/Super Mario Bros. (W) [!].nes"
IN=data/wr/wr_inputs.bin
S="${SECS:-10800}"
# 1-2 is the level where the target byte matters (its warp zone reads WarpZoneControl).
systemd-run --user --scope -q -p MemoryMax=1800M --unit e6-w12 -- \
  ./build/explore "$CORE" "$ROM" "$IN" --root 2483 --horizon 1290 \
  --max-addr 0x300 --max-weight 20 --prog-fw 1 \
  --cells 100000 --rollout 6,50 --enemycell 0 --xcell 8 --ycell 16 --spdcell 16 --relcell 32 \
  --seed 71 --secs "$S" --report 180 --out runs/E6-vram > runs/E6-vram/w12.log 2>&1 &
# 4-2 has the densest brick rows on the route (page 10: RowOfBricks len 9 over RowOfCoins len 9).
systemd-run --user --scope -q -p MemoryMax=1800M --unit e6-w42 -- \
  ./build/explore "$CORE" "$ROM" "$IN" --root 6582 --horizon 700 \
  --max-addr 0x300 --max-weight 20 --prog-fw 1 \
  --cells 100000 --rollout 6,50 --enemycell 0 --xcell 8 --ycell 16 --spdcell 16 --relcell 32 \
  --seed 72 --secs "$S" --report 180 --out runs/E6-vram > runs/E6-vram/w42.log 2>&1 &
echo "launched e6-w12 e6-w42 -> runs/E6-vram/*.log"
