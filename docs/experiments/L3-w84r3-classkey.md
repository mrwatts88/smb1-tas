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
