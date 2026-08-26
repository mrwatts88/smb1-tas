#!/bin/sh
# L3 / H25 — 8-4 room 3, PHASE 2: the exhaustive continuation.
#
# Phase 1 (runs/L3-w84r3/launch.sh, approach.log) finished 2026-08-25 s22 in 1640.8s and stopped at
# --stop-step 162 with **5,225 apex candidates** in layer_162.bin (F133(d) kept 2,303, F133(e) 4,333 —
# but on a key missing four of the six XPosState fields; this one carries the `cls` axis, F272).
# No goal in phase 1, which is expected: the goal is in the return leg, past step 162.
#
# THE QUESTION: is a return class costing R=33 reachable at step <= 161?  The WR crosses into a class
# paying 34 and the floor is 33.  One frame — and in 8-4 one frame IS the record (H24).
#
# A goal at <= 194 is H25's frame: replay on the core (tools/e3_replay.py), CHECK THE DESTINATION not
# the goal flag (runbook §4.3), then sync in FCEUX + BizHawk before it is called anything.
# Dry = a negative for this candidate set only (layers 1..162 are still beamed), but from a key that
# CAN represent the answer — which is what the two earlier negatives could not claim.
#
# Both earlier exhaustive continuations died at layer 188, byte-identically.  If this one does the same
# the verdict is "the continuation is too wide", not "no frame exists" — say so in that language.
cd /home/mattwatts/Documents/smb1-tas || exit 1
BIN=third_party/smb-opt/target/release/smb-opt
LOG=runs/L3-w84r3/phase2.log
systemd-run --user --scope -p MemoryMax="${MEMMAX:-10G}" -p MemorySwapMax=0 --quiet \
  "$BIN" bfscx W84Room3 data/wr/wr_inputs.bin 16354 0 194 \
    --threads 8 --acc-mb 96 --resume 162 \
    --layer-dir runs/L3-w84r3/approach_layers >> "$LOG" 2>&1 &
SPID=$!
sh tools/watchdog.sh "$SPID" "$LOG" 200000000 40 >> runs/L3-w84r3/phase2_watchdog.log 2>&1 &
echo "L3 phase2 search $SPID watchdog $!"
