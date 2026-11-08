#!/bin/sh
# H52 follow-up: the 12 one-frame substitutions that delay Bowser's spawn (sweep.tsv: spawn core
# 17755-17759 vs the WR's 17754) all die in the --ending-scan family, which keeps the WR's hop at
# 17782.  Here each gets the full two-jump enumeration (re-timed hop), j1 17776..17786.
# ~19 min per j1 => ~3.5 h per process, 12 processes.  Read:
#   grep -h "RECORD\|TOTAL\|j1=" runs/H52-spawn/tj_*.log
cd "$(dirname "$0")/../.."
CORE=third_party/QuickNES_Core/quicknes_libretro.so
ROM="roms/Super Mario Bros. (W) [!].nes"
go() { # go T PAD
  systemd-run --user --scope -q -p MemoryMax=1000M --unit "h52tj-$1-$2" -- \
    ./build/ram_oracle "$CORE" "$ROM" data/wr/wr_inputs.bin --input-skip 2 --set-input "$1=$2" \
    --two-jump 17760 --j1 17776:17786 > "runs/H52-spawn/tj_$1_$2.log" 2>&1 &
  echo "launched h52tj-$1-$2"
}
go 17743 128
go 17743 194
go 17744 194
go 17745 194
go 17746 194
go 17747 194
go 17748 194
go 17749 194
go 17750 194
go 17751 194
go 17752 194
go 17753 194
