# L8 — E6's six roots re-run with the object-slot lens (launched 2026-11-12 19:57 CST, Fedora box)

Command: `sh runs/L8-e6-objectlens/launch.sh` (copy of runs/E6-vram/launch.sh with the output directory changed;
build/explore rebuilt from commit 3d6a6a4, which has anomaly classes 17/18 and the F301 death fix).
Six processes (systemd scopes l8-w12, l8-w42, l8-w11, l8-w41, l8-w82, l8-w83), 1.5 GB cap each, 21,600 s each:
expected to finish about 2026-11-13 01:58 CST.
Read: `grep -h 'anom=\|ANOM\|done' runs/L8-e6-objectlens/w*.log | tail`; each hit dumps a .path file in this
directory; replay with tools/e3_replay.py. Verdict goes in docs/experiments/L8-e6-objectlens.md: per root the
anom mask, every class-17/18 hit replayed and triaged, and the classes that did not fire.
