#!/usr/bin/env python3
"""P2.5c-2 — check the Rust 4-2 enemy module (`smb-opt tracec W42Main … --enemies`) against the WR dump, slot by slot.

Runs the model on the WR's records from FIRST for N steps and compares, per frame, the live enemy slots it prints
("slots: … | sI idXX stXX xN yN spdXX fXX dD itN ftN mM cbXX ysXX yfXX") with the dump's slots 0–4 (rows = record + 2,
F45). Items (mushroom $2E / vine $2F, H34) are not modelled: they are skipped in the dump, and because their slots
are free in the model, slot *indices* can differ from the dump (e.g. plant B takes slot 1 instead of 2 after the
vine bump) — so the comparison is by multiset of (id, state, x, y, speed, force, dir, timer) over the live
non-item, non-lift slots (a plant's stale Enemy_X_MoveForce, inherited from the slot's previous occupant, is ignored: it never moves horizontally). A plant the model spawns in the wrong-warp pipe (col 84) where the dump had none is the
expected consequence of the missing vine (F100) and is counted separately.

Usage: tools/w42_enemy_check.py [--first 6584] [--n 588] [--ram data/wr/fceux_wr.ram] [--verbose]
"""
import os, re, subprocess, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
_argv = sys.argv; sys.argv = sys.argv[:1]
from ram_trace import load_symbols  # noqa: E402
sys.argv = _argv
SYMS = load_symbols()
SMBOPT = "third_party/smb-opt/target/release/smb-opt"
SLOT_RE = re.compile(r"s(\d) id([0-9a-f]{2}) st([0-9a-f]{2}) x(\d+) y(\d+) spd([0-9a-f]{2}) f([0-9a-f]{2}) d(\d) it(\d+) ft(\d+) m(\d) cb([0-9a-f]{2}) ys([0-9a-f]{2}) yf([0-9a-f]{2})")


def A(name, n=0):
    return SYMS[name] + n


def main():
    opt = dict(first=6584, n=588, ram="data/wr/fceux_wr.ram", verbose=False)
    args = sys.argv[1:]; i = 0
    while i < len(args):
        k = args[i].lstrip("-")
        if k == "verbose": opt[k] = True; i += 1; continue
        opt[k] = int(args[i + 1]) if k in ("first", "n") else args[i + 1]; i += 2
    data = open(opt["ram"], "rb").read()
    r = lambda row, a: data[(row - 1) * 2048 + a]
    out = subprocess.run([SMBOPT, "tracec", "W42Main", "data/wr/wr_inputs.bin", str(opt["first"]), str(opt["n"]), "--enemies", "0"],
                         check=True, capture_output=True, text=True).stdout
    lines = out.splitlines()
    model = {}
    step = None
    for line in lines:
        if line and line[0].isdigit():
            step = int(line.split()[0])
        elif line.startswith("slots:") and step is not None:
            model[step] = [dict(slot=int(m.group(1)), id=int(m.group(2), 16), st=int(m.group(3), 16), x=int(m.group(4)), y=int(m.group(5)),
                                spd=int(m.group(6), 16), f=int(m.group(7), 16), d=int(m.group(8)), it=int(m.group(9)), ft=int(m.group(10)),
                                m=int(m.group(11)), cb=int(m.group(12), 16)) for m in SLOT_RE.finditer(line)]
    bad, extra_plants, compared = 0, 0, 0
    for step in sorted(model):
        row = opt["first"] + step + 2
        dump = []
        for k in range(5):
            if not r(row, A("Enemy_Flag", k)): continue
            eid = r(row, A("Enemy_ID", k))
            if eid in (0x2e, 0x2f, 0x27): continue
            timer = r(row, A("EnemyFrameTimer", k)) if eid == 0x0d else r(row, A("EnemyIntervalTimer", k))
            # A plant's Enemy_X_MoveForce AND Enemy_MovingDir are stale slot memory (never read by MovePiranhaPlant
            # or the collisions) — and dir 0 (never-set RAM, e.g. pipe C spawning into the killed vine's slot) is
            # unrepresentable in the record's 1-bit dir. Ignore both for plants.
            dump.append((eid, r(row, A("Enemy_State", k)), r(row, A("Enemy_PageLoc", k)) * 256 + r(row, A("Enemy_X_Position", k)),
                         r(row, A("Enemy_Y_Position", k)), r(row, A("Enemy_X_Speed", k)), 0 if eid == 0x0d else r(row, A("Enemy_X_MoveForce", k)),
                         0 if eid == 0x0d else r(row, A("Enemy_MovingDir", k)), timer,
                         0 if eid == 0x0d else int(r(row, A("EnemyOffscrBitsMasked", k)) != 0)))   # plants: masked is stale at the spawn instant and recomputed from the compared x/screen afterwards
        mod = []
        mod_vine = False
        for s in model[step]:
            if s["id"] in (0x2e, 0x27): continue
            if s["id"] == 0x2f:
                # H34: the model's vine objects. The injected occupant's x/y are garbage copies in the real game
                # (Setup_Vine off an arbitrary Y), so compare PRESENCE in slots 0-4 only, not coordinates.
                if s["slot"] < 5: mod_vine = True
                continue
            if s["id"] == 0x0d and s["x"] == 84 * 16 + 8:
                extra_plants += 1; continue
            mod.append((s["id"], s["st"], s["x"], s["y"], s["spd"], 0 if s["id"] == 0x0d else s["f"], 0 if s["id"] == 0x0d else s["d"], s["ft"] if s["id"] == 0x0d else s["it"], 0 if s["id"] == 0x0d else s["m"]))
        dump_vine = any(r(row, A("Enemy_Flag", k)) and r(row, A("Enemy_ID", k)) == 0x2f for k in range(5))
        compared += 1
        if sorted(dump) != sorted(mod) or dump_vine != mod_vine:
            bad += 1
            if bad <= 30 or opt["verbose"]:
                print(f"row {row} (step {step}): model {sorted(mod)} vine={mod_vine} vs dump {sorted(dump)} vine={dump_vine}")
    print(f"{bad} mismatching rows over {compared} compared (model rows {opt['first'] + 2}..{opt['first'] + 1 + len(model)}); wrong-warp-pipe plant rows in the model (should be 0 with the H34 vine; F100): {extra_plants}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
