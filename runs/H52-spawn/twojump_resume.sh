#!/bin/sh
# H52 follow-up, resume after the 2026-11-08 ~12:15 kill.  twojump.sh had finished j1 17776-17777
# for every variant and 17778 for four of them (tj_*.log).  This runs the remaining j1 values into
# tj_*.r2.log so the first logs are kept.  Read:
#   grep -h "RECORD\|TOTAL\|j1=" runs/H52-spawn/tj_*.log
cd "$(dirname "$0")/../.."
CORE=third_party/QuickNES_Core/quicknes_libretro.so
ROM="roms/Super Mario Bros. (W) [!].nes"
go() { # go T PAD J1LO
  systemd-run --user --scope -q -p MemoryMax=1000M --unit "h52tjr-$1-$2" -- \
    ./build/ram_oracle "$CORE" "$ROM" data/wr/wr_inputs.bin --input-skip 2 --set-input "$1=$2" \
    --two-jump 17760 --j1 "$3:17786" > "runs/H52-spawn/tj_$1_$2.r2.log" 2>&1 &
  echo "launched h52tjr-$1-$2 from j1=$3"
}
go 17743 128 17779
go 17743 194 17778
go 17744 194 17778
go 17745 194 17778
go 17746 194 17778
go 17747 194 17779
go 17748 194 17779
go 17749 194 17779
go 17750 194 17778
go 17751 194 17778
go 17752 194 17778
go 17753 194 17778
