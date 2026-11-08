#!/bin/sh
# H51 two-jump enumeration (ram_oracle --two-jump): every hop start 17770..17800 x hop hold 1..40
# x hop pad {A, A+R} x between-jump fill/tail variants x final jump start 17815..17850 x hold
# (last input <= 17850).  See the comment block at `two_jump` in src/fastcore/ram_oracle.c.
# Control (j1 = 17782, the WR's hop): 251,400 runs, WR combo reaches the axe at last 17846,
# best 17846, 0 record candidates, 18.8 min single-threaded.
# 2026-11-08 first launch (3 j1 per process): j1 >= 17785 dies before the hop with the B+R
# pre-fill, and 17783/17784 produce no surviving run, so only 17770..17781 carry work; relaunched
# one j1 per process.  Results of the first launch for 17783..17800 are in s05..s10.log.
# Usage: ./runs/H51-twojump/launch.sh      Read: grep -h "RECORD\|TOTAL\|j1=" runs/H51-twojump/*.log
cd "$(dirname "$0")/../.."
CORE=third_party/QuickNES_Core/quicknes_libretro.so
ROM="roms/Super Mario Bros. (W) [!].nes"
go() { # go TAG J1RANGE
  systemd-run --user --scope -q -p MemoryMax=1000M --unit "h51tj-$1" -- \
    ./build/ram_oracle "$CORE" "$ROM" data/wr/wr_inputs.bin --input-skip 2 --two-jump 17760 --j1 "$2" \
    > "runs/H51-twojump/$1.log" 2>&1 &
  echo "launched h51tj-$1 j1=$2"
}
case "${PHASE:-2}" in 1)
go s01 17770:17772
go s02 17773:17775
go s03 17776:17778
go s04 17779:17781
go s05 17783:17785
go s06 17786:17788
go s07 17789:17791
go s08 17792:17794
go s09 17795:17797
go s10 17798:17800
;;
*)
go t01 17770
go t02 17771
go t03 17772
go t04 17773
go t05 17774
go t06 17775
go t07 17776
go t08 17777
go t09 17778
go t10 17779
go t11 17780
go t12 17781
;;
esac
