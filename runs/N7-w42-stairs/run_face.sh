#!/bin/sh
# usage: run_face.sh CLIPFROM TAG   (WR movie, root 7440, one-frame budget through x 790)
cd "$(dirname "$0")/../.."
./build/endlab third_party/QuickNES_Core/quicknes_libretro.dylib roms/smb.nes runs/N7-w42-stairs/wr_inputs.bin --input-skip 2 \
  --pads 0x82,0x83 --clip --clipfrom "$1" --through 790 64 --flag 7440 7570 --xline 789 7568 \
  --out "runs/N7-w42-stairs/$2" --maxnodes 4000000 > "runs/N7-w42-stairs/$2.log" 2>&1
