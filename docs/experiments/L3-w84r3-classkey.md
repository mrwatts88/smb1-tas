# L3 / H25 — the room-3 negatives rest on a beam key that cannot see the answer

**Unit:** L3 (`docs/open-threads.md`). Linux box, 2026-08-25 session 21.

## 1. The question, unchanged since F133

8-4 room 3 = (steps to first cross `x >= 3457`) + (return to the pipe). `build_overshoot_bound` reports
**30,720 end classes** with **7 distinct return costs [33..39]**. The WR crosses at step 161 into a class
paying **34**; the floor is **33**. So the whole room reduces to: **is a 33-cost end class reachable at
step <= 161?** One frame — and 8-4 is the only level where one frame *is* the record.

## 2. What the 33-cost classes actually are — nobody had looked

`SMBOPT_DUMP_ENDCLASSES=1` (added this unit; prints the class envelope per return cost):

```
ENDCLASS R=33 n=1280  x_spd [0x0100..0x0afc] (1.00..10.98 px/frame) abs [0..0]  ground 1280 air 0  running 1280 walking 0
ENDCLASS R=34 n=6149  x_spd [0x0100..0x22cc] (1.00..34.80)          abs [0..33] ground 2805 air 3344 running 6053 walking 96
ENDCLASS R=35 n=13493 x_spd [0x0bd0..0x28fc] (11.81..40.98)         abs [11..33] …
```

Every one of the 1,280 cheapest classes is **on the ground, `running_speed` set, `x_spd_abs` = 0, moving
RIGHT at 4.8–11 px/frame, facing LEFT** (individual dumps: `mdir RIGHT fdir LEFT`, some `fdir LEFT|RIGHT|LR`
— i.e. L+R). That combination is a **landing frame**: `x_spd_abs` is stale at 0 because `ImposeFriction`
does not run airborne unless L/R is held, and `PlayerBGCollision` sets `Player_State = 0` *after* the
movement subs. So the cheapest return in this room is available only to a state that has just touched down
past the pipe, slowly, already facing left.

## 3. Why the two existing negatives do not answer the question

F133(d)/(e) ran diversity beams keyed **`off,y,spd,sub,vf`**, kept 2,303 then 4,333 apex candidates, and
both exhaustive continuations died at layer 188 — byte-identically. F133(d) justified the beam:

> "the beam ranks by h *within* each physical bucket and the return cost is a function of the bucketed
> variables (x-class = speed × subpixel, plus y), so the beam should retain the h-minimal representative of
> each class"

**That is false.** The class is

```rust
XPosState = (x_spd, x_spd_abs, moving_dir, facing_dir, is_on_ground, running_speed)
```

and the bucket key contained **none of the last four**. `spd` bands `x_spd` at 4 px/frame and `sub` is the
subpixel phase of `x_pos`, not of the speed. So two states with the same speed band and y but *different
return costs* competed for one slot and were ranked by `h` — which prefers the **faster** state, while the
R=33 profile is the slow one. Both runs made the same omission, which is precisely why widening the beam 5×
and adding a fifth axis produced **identical** death behaviour: more of the same blind spot is still blind.

This does not make F133 wrong about what it measured. It makes its *soundness argument* wrong, and with it
the reason anyone treated the room as closed.

## 4. The fix, and the control

New `--beam-buckets` axis **`cls`** carrying `(x_spd_abs, moving_dir, facing_dir, is_on_ground,
running_speed)` — exactly the class tail the key was missing (`x_spd` itself stays covered by `spd`/`sub`).

Engine control gate after the change, byte-identical to the standing values:

```
bfscx W42Main data/wr/wr_inputs.bin 6584 575 587 --lift 0 --check-path 12
  -> 6, 16, 34, 70, 134, 673, 3472, 16472, 69489, 257001   ✓
```

## 5. The run

`runs/L3-w84r3/launch.sh` — phase 1, the approach to step 162 keyed
`off,y,spd,sub,vf,cls`, `--beam 250 --beam-max 3000000`, under `MemoryMax=10G`. Early layers show **2,180
buckets** against the old key's far smaller count, which is the axis doing its job.

Phase 2, once phase 1 stops at 162:

```
smb-opt bfscx W84Room3 data/wr/wr_inputs.bin 16354 0 194 --threads 8 --acc-mb 96 --resume 162 \
    --layer-dir runs/L3-w84r3/approach_layers
```

**A goal at <= 194 is H25's frame** — replay on the core, destination-check, then FCEUX + BizHawk.
**Dry** is a negative for this candidate set only (layers 1–162 are still beamed), but for the first time
from a key that *can* represent the answer.

---

## 6. Result (session 22, 2026-08-25) — DRY, and this time the key could have seen it

### Phase 1 — the corrected approach beam

Ran to completion in **1640.8 s** and stopped at `--stop-step 162` as designed:

```
layer 162: parents 4102 -> unique 5225, generated 21864, pruned 43768, dead 0, other 0, goals 0
stopping at step 162 (--stop-step)
total 1640.8s
```

**5,225 apex candidates** carried into phase 2, against F133(d)'s 2,303 and F133(e)'s 4,333. No goal in
phase 1, which is expected — the goal lives past step 162, in the return leg.

### Phase 2 — the exhaustive continuation

`runs/L3-w84r3/launch_phase2.sh` (the documented resume command, wrapped in `systemd-run
MemoryMax=10G MemorySwapMax=0` plus `tools/watchdog.sh`, per the standing rule). It finished in
**11.9 s**:

```
layer 187: parents 242653 -> unique 23084, generated 85568, pruned 3796880, ... max x 0xd5e70
layer 188: parents 23084 -> unique 0, generated 0, pruned 369344, ... max x 0x0
no live states left after layer 188
no goal found within 194 steps
```

The frontier is **bound-pruned to zero**, not killed by memory or by the watchdog. Within this
candidate set, nothing can cross the threshold and return to the pipe by step 194.

### Did the `cls` axis actually bite?

This is the question the unit exists to answer, so it is worth the comparison. Against the two earlier
negatives (`runs/P2.2a-prime/return.log`, `return2.log`):

| layer | F133(d) unique | F133(e) unique | **s22 `cls`** | max x (all three) |
|---|---|---|---|---|
| 185 | 86,322 | 151,546 | **151,752** | 0xd6310 |
| 186 | 138,340 | 242,207 | **242,653** | 0xd60d0 |
| 187 | 12,164 | 23,736 | **23,084** | 0xd5e70 |
| 188 | 0 | 0 | **0** | — |

The counts differ from both — so the retained set is genuinely different, and the axis is not inert —
while `max x` per layer is identical and all three collapse at exactly layer 188. **A different
candidate set reaches the same wall.**

### The target class, from the bound's own census

`SMBOPT_DUMP_ENDCLASSES=1 ... --check-path 12` (`runs/L3-w84r3/endclasses.log`):

```
overshoot bound: threshold x 0xd8100, return to x <= 0xd4cff; 30720 end classes, 7 distinct costs [33..39]
ENDCLASS R=33 n=1280 x_spd [0x0100..0x0afc] (px/frame 1.00..10.98) abs [0..0] ground 1280 air 0 running 1280 walking 0
ENDCLASS R=34 n=6149 x_spd [0x0100..0x22cc] (px/frame 1.00..34.80) abs [0..33] ground 2805 air 3344 ...
```

All 1,280 minimum-cost classes are `mdir RIGHT`, mostly `fdir LEFT`, `ground true`, `running true`,
`abs 0` — the landing frame F272 predicted. The WR crosses into an R=34 class; the floor is 33.

## 7. Verdict, stated at the width the evidence supports

**H25 is dry for the third time, and for the first time from a key that carries the whole return
class.** What is refuted is: *no R=33 end class is reachable at step ≤ 161 through a state this beam
retains.* Layers 1–162 are still beamed at 250 per bucket, so this is a negative for the beamed
candidate set — **not a proof that the frame does not exist**, and it must not be written down as one.

What would raise it to a proof is the same thing it has always been: an unbeamed approach, which is a
state-space problem (F98's law), not a key problem. The key defect F272 identified is now closed.

## 8. Parked (user decision, 2026-08-25 s22)

The honest remaining lever was the *width* of phase 1, not its key — `--beam 250` on 3,977 buckets keeps
5,225 survivors out of ~12M generated per layer. **The user's call: no more widening.** "I'm done widening
beams. I'm done just searching further into the abyss."

That is the right call on the evidence, and worth recording *why* rather than just that it happened. This
hypothesis has now had each of its three structural objections closed in turn:

1. **F125 / H39** — an approach goaled on the WR's apex can only find "reach the WR's apex sooner", and the
   WR's apex is already proven not to yield the frame. → L3 emitted a **set** of 5,225 apexes and continued
   every one exhaustively. Closed.
2. **F272** — the beam key contained none of `x_spd_abs, moving_dir, facing_dir, is_on_ground,
   running_speed`, four of the six fields the return cost depends on. → the `cls` axis, verified above to
   have genuinely changed the retained set. Closed.
3. **Width.** Not a structural objection at all — just more search.

When the only thing left is (3), the thread is done. Three independent negatives, the last from a key that
could represent the answer, for **one frame**.

**What would reopen it is a different primitive, not a bigger search.** The 1,280 R=33 end classes are
*already enumerated* (`runs/L3-w84r3/endclasses.log`). A **backward** reachability from those classes to a
step ≤ 161 state answers H25 directly and is goal-directed rather than a forward beam — it does not delete
the slow landing states, because it starts from them. The engine has no such primitive and nobody should
build one for a single frame. But if a backward primitive is ever built for another reason, **H25 reopens
for free** and the target set is sitting on disk.

`runs/L3-w84r3/approach_layers` (19 GB) was deleted; `launch.sh` regenerates it in 27 minutes.
