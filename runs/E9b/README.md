# runs/E9b — the two live sites from the E9a census

`docs/experiments/P4E-census.md` §6 is the shortlist. This directory holds part 1: **8-2's
columns 201-212**, priced at 114 frames by F245 and posed exactly by H48.

**Not yet launched.** At the time E9a closed, four `build/explore` archives (`runs/E7-w12/*`,
`runs/E8-w82/climb.log`) were running and the box had **1 GB available of 15 GB with swap 5/7
used** — no headroom for a fifth. Start these only after `pgrep -x explore` is empty.

    ./runs/E9b/launch.sh          # 6 h each, two archives, MemoryMax=2200M via systemd-run

**How to read the result.** `grep GOAL runs/E9b/*.log`; the control reproduces **12953**, a banked
frame is anything below it, **a record is core <= 12931**. Replay with
`tools/e3_replay.py FILE --around N`, check the level actually ends earlier (`StarFlagTaskControl`
== 5, not the pole grab — F230/F237), then sync in FCEUX + BizHawk.

**The specific thing being hunted** (H48, and it is a 1-2 px question — hence `--subcell`): a
pillar landing at **x <= 3252 with speed >= 39**, from which the WR's own measured full-speed arc
clears the col-206/207 wall with 10-25 px of margin instead of missing by 1-2 px. The approach jump
that produces that landing must still clear the col-199/201 staircase (top row 8, `Y` = 128; the WR
passes it at y 126). If the archives go dry, the fallback is the direct probe: splice a jump into
the WR inputs at dump 12289 and replay on the core.
