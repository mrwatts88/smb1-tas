#!/bin/sh
# N1 (F305-F310): rebuild the "enter the Bowser room one frame late" candidate from the WR inputs
# and replay it.  ~3 minutes.  Usage: tools/n1_build_candidate.sh [CORE] [ROM]
# Expect:  stage 2 "BEST last input = core 17843 (WR 17846)" and
#          "replay: victory_core=17865  last_nonzero_input_core=17843".
set -e
cd "$(dirname "$0")/.."
case "$(uname -s)" in
  Darwin) DCORE=third_party/QuickNES_Core/quicknes_libretro.dylib ;;
  *)      DCORE=third_party/QuickNES_Core/quicknes_libretro.so ;;
esac
CORE="${1:-$DCORE}"
ROM="${2:-roms/Super Mario Bros. (W) [!].nes}"
[ -f "$ROM" ] || ROM=roms/smb.nes
OUT=runs/N1-ending
mkdir -p "$OUT" data/candidates
# control: the unmodified scene is closed at the WR's last input (58 s)
./build/endlab "$CORE" "$ROM" data/wr/wr_inputs.bin --input-skip 2 --bfs 17760 17862 --coast 17815 17852 > "$OUT/ctl.log"
grep -E "scene|BEST" "$OUT/ctl.log"
# stage 1: one blank frame at the water-room pipe (core 17412) = room entered one frame late;
# find a full-speed route through the first half of the room and stop on the ground at 17750
./build/endlab "$CORE" "$ROM" data/wr/wr_inputs.bin --input-skip 2 --insert 17412=0x00 \
    --bfs 17625 17760 --ground-at 17750 --pick 0 --out "$OUT/k1_stage1.bin" > "$OUT/k1_stage1.log"
grep -E "checkpoint|picked" "$OUT/k1_stage1.log"
# stage 2: exhaustive jump-timing search of the ending in that scene
./build/endlab "$CORE" "$ROM" "$OUT/k1_stage1.bin" --input-skip 2 --bfs 17750 17868 --coast 17812 17856 \
    --out "$OUT/k1_best.bin" > "$OUT/k1_stage2.log"
grep -E "scene|SUCCESS|BEST" "$OUT/k1_stage2.log"
./build/endlab "$CORE" "$ROM" "$OUT/k1_best.bin" --input-skip 2 --replay
# fm2 that ends on its last input (movie bytes 17414..17845 differ from the WR)
dd if="$OUT/k1_best.bin" of="$OUT/k1_seg.bin" bs=1 skip=17414 count=432 2>/dev/null
python3 tools/splice_fm2.py "data/wr/happylee-supermariobros,warped.fm2" "$OUT/k1_seg.bin" 17414 \
    "$OUT/n1_rebuilt.fm2" --pad 0
cmp "$OUT/n1_rebuilt.fm2" data/candidates/smb1-warps-n1-17846.fm2 && echo "identical to data/candidates/smb1-warps-n1-17846.fm2"
