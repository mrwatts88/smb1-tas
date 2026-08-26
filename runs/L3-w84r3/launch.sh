#!/bin/sh
# L3 / H25 — 8-4 room 3, the approach beam re-run with a key that can SEE the return cost.
#
# THE QUESTION (F133c, unchanged): the room is (steps to first cross x >= 3457) + (return to the pipe).
# `build_overshoot_bound` reports 30,720 end classes with 7 distinct return costs [33..39]; the WR crosses
# at step 161 into a class paying **34**, and the floor is **33**.  So: is a 33-cost end class reachable
# at step <= 161?  One frame, in the only level where one frame is the record.
#
# WHY THE TWO EXISTING NEGATIVES DO NOT ANSWER IT (2026-08-25).  F133(d)/(e) ran diversity beams keyed
# `off,y,spd,sub,vf` and kept 2,303 then 4,333 apex candidates; both exhaustive continuations died at
# layer 188, byte-identically.  F133(d) justified the beam like this: "the return cost is a function of
# the bucketed variables (x-class = speed x subpixel, plus y), so the beam should retain the h-minimal
# representative of each class."  **That is false.**  The class is
#     XPosState = (x_spd, x_spd_abs, moving_dir, facing_dir, is_on_ground, running_speed)
# and the beam key contained NONE of the last four.  States with the same speed band and y but different
# return costs competed for one slot, ranked by h -- which prefers the FASTER state.  And the R=33 profile
# is the slow one:
#     SMBOPT_DUMP_ENDCLASSES=1 ... -> ENDCLASS R=33 n=1280 x_spd [0x0100..0x0afc] (1.00..10.98 px/frame)
#                                    abs [0..0] ground 1280 air 0 running 1280 walking 0
# i.e. **on the ground, moving right at 4.8-11 px/frame, facing LEFT, running_speed set, x_spd_abs = 0** --
# a LANDING frame (abs is stale because ImposeFriction does not run airborne without L/R, and the collision
# sets Player_State = 0 after the movement subs).  A beam ranked on h never keeps one.  Both negatives made
# the same omission, which is exactly why widening 5x changed nothing.
#
# THE FIX: `cls`, a new --beam-buckets axis carrying (x_spd_abs, moving_dir, facing_dir, is_on_ground,
# running_speed) -- the whole class tail the key was missing.  Control gate after the engine change is green
# (W42Main 6584 575 587 --check-path 12 -> 6, 16, 34, 70, 134, 673, 3472, 16472, 69489, 257001).
#
# PHASE 1 (this script): the approach to step 162, beamed on the corrected key.
# PHASE 2: exhaustive continuation from every surviving apex to deadline 194 --
#   smb-opt bfscx W84Room3 data/wr/wr_inputs.bin 16354 0 194 --threads 8 --acc-mb 96 --resume 162 \
#     --layer-dir runs/L3-w84r3/approach_layers
# A goal at <= 194 is H25's frame: replay it on the core, check the destination, then two emulators.
# Dry = a negative for this candidate set only (layers 1..162 are still beamed) -- but a negative from a key
# that CAN see the answer, which is not what we had before.
cd /home/mattwatts/Documents/smb1-tas || exit 1
BIN=third_party/smb-opt/target/release/smb-opt
LOG=runs/L3-w84r3/approach.log
systemd-run --user --scope -p MemoryMax=10G -p MemorySwapMax=0 --quiet \
  "$BIN" bfscx W84Room3 data/wr/wr_inputs.bin 16354 0 194 \
    --threads 8 --acc-mb 96 --stop-step 162 \
    --beam "${BEAM:-250}" --beam-buckets off,y,spd,sub,vf,cls --beam-max "${BEAMMAX:-3000000}" \
    --layer-dir runs/L3-w84r3/approach_layers >> "$LOG" 2>&1 &
SPID=$!
sh tools/watchdog.sh "$SPID" "$LOG" 200000000 40 >> runs/L3-w84r3/approach_watchdog.log 2>&1 &
echo "L3 approach search $SPID watchdog $!"
