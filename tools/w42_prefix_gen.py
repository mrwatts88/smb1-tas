#!/usr/bin/env python3
"""P2.5c-2 — generate input prefixes that put Mario in a chosen region of 4-2's main area, for enemy-dense core
difftests (`tools/model_difftest.py --prefix-dir DIR`).

Random right-biased trajectories with A held in runs (the generator of tools/ygate_audit.py) are replayed in the
model from a root record (the WR's records before it) with `smb-opt traceh` (batched, lift hook only: the enemies
cannot touch Mario before the region's first enemy spawn, and the candidates are re-checked below) and cut at the
first step where x >= GX and Player_Y <= GY hold. Each candidate is re-traced with `tracec --enemies APTN0` and
kept only if (1) no item cell ((28,7) (55,7) (81,7) (64,3): H34, unmodelled spawns) was bumped, (2) Mario is alive
and no enemy event happened (so the prefix itself is exact on the core regardless of the enemy module). Survivors
are written as full input files (records 0..) to OUT_DIR/NAME_NNNN.bin with an index OUT_DIR/NAME.txt
(file, records, step, x, Y, state, slots).

Usage: tools/w42_prefix_gen.py --out DIR --name topfloor --root 6584 --gx 480 --gy 112 [--n 2000] [--len 300]
         [--seed 1] [--max 60] [--pr .85 --pl .05 --pa .2 --amax 30 --pb .8] [--first 6584] [--aptn0 0]
         [--min-step S]   (the goal must first hold after step S from the case root; default = root - first + 1)
         [--allow-used MASK]  item-cell bits of `blocks.used` tolerated in the prefix (e.g. 0x80 = the WR's (28,7)
                          mushroom bump at ~6780, harmless for slot occupancy: gone by 6889, before the lift spawns)
"""
import os, random, re, subprocess, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import model_difftest as md
from ygate_audit import gen_random, ROW_RE as H_ROW_RE

ITEM_MASK = (1 << 3) | (1 << 7) | (1 << 11) | (1 << 15)   # W42MainBlocks::CELLS: (64,3) (28,7) (55,7) (81,7)
BLOCKS_RE = re.compile(r"^blocks: bounce \d+ used (0x[0-9a-f]+|\d+) ")


def traceh_batch(case, first, n, gx, gy, aptn0, paths):
    cmd = [md.SMBOPT, "traceh", case, str(first), str(n), "--lift", str(aptn0), "--goal-x", str(gx), "--goal-y", str(gy)] + paths
    out = subprocess.run(cmd, check=True, capture_output=True, text=True).stdout
    res, cur = {}, None
    for line in out.splitlines():
        if line.startswith("=== "):
            cur = line[4:]; res[cur] = None
            continue
        m = H_ROW_RE.match(line)
        if m and cur is not None and res[cur] is None and m.group(8) == "1":
            res[cur] = int(m.group(1))
    return res


def tracec_check(case, path, first, steps, aptn0, allow=0):
    """Replay `steps` records from `first` with the enemy hook; returns (alive_and_clean, last_row, slots, used)."""
    cmd = [md.SMBOPT, "tracec", case, path, str(first), str(steps), "--enemies", str(aptn0)]
    out = subprocess.run(cmd, check=True, capture_output=True, text=True).stdout
    last, slots, used, clean = None, "", 0, True
    for line in out.splitlines():
        m = md.ROW_RE.match(line)
        if m:
            last = line
            r = m.group(10)
            if "DEATH" in r or "STOMP" in r or "KICK" in r or not r.startswith("Success"): clean = False
            continue
        b = BLOCKS_RE.match(line)
        if b: used = int(b.group(1), 0)
        if line.startswith("slots:"): slots = line[7:]
        if line.startswith("stopped"): clean = False
    if used & ITEM_MASK & ~allow: clean = False
    return clean, last, slots, used


def main():
    opt = dict(out=None, name="pfx", root=6584, first=6584, gx=None, gy=None, n=2000, len=300, seed=1, max=60,
               pr=.85, pl=.05, pa=.2, amax=30, pb=.8, aptn0=0, case="W42Main", batch=50, min_step=None, allow_used=0)
    args = sys.argv[1:]; i = 0
    while i < len(args):
        k = args[i].lstrip("-").replace("-", "_"); v = args[i + 1]; i += 2
        if k in ("out", "name", "case"): opt[k] = v
        elif k in ("pr", "pl", "pa", "pb"): opt[k] = float(v)
        else: opt[k] = int(v, 0)
    assert opt["out"] and opt["gx"] is not None and opt["gy"] is not None, "--out, --gx, --gy are required"
    os.makedirs(opt["out"], exist_ok=True)
    wr = open(md.WR, "rb").read()
    prefix0 = wr[:opt["root"]]
    root_step = opt["root"] - opt["first"]
    min_step = opt["min_step"] if opt["min_step"] is not None else root_step + 1
    rng = random.Random(opt["seed"])
    tmp = os.path.join(opt["out"], "tmp"); os.makedirs(tmp, exist_ok=True)
    index = open(os.path.join(opt["out"], opt["name"] + ".txt"), "w")
    kept, tried, reached, rejected = 0, 0, 0, dict(item=0, event=0, early=0)
    while tried < opt["n"] and kept < opt["max"]:
        paths = []
        for b in range(opt["batch"]):
            rec = gen_random(rng, opt["len"], opt["pr"], opt["pl"], opt["pa"], opt["amax"], opt["pb"])
            p = os.path.join(tmp, "c%05d.bin" % (tried + b))
            open(p, "wb").write(prefix0 + rec); paths.append(p)
        tried += len(paths)
        hits = traceh_batch(opt["case"], opt["first"], root_step + opt["len"], opt["gx"], opt["gy"], opt["aptn0"], paths)
        for p in paths:
            g = hits.get(p)
            if g is None: continue
            reached += 1
            if g < min_step: rejected["early"] += 1; continue
            cut = os.path.join(tmp, "cut.bin")
            data = open(p, "rb").read()[: opt["first"] + g]
            open(cut, "wb").write(data)
            clean, last, slots, used = tracec_check(opt["case"], cut, opt["first"], g, opt["aptn0"], opt["allow_used"])
            if not clean:
                rejected["item" if used & ITEM_MASK & ~opt["allow_used"] else "event"] += 1; continue
            name = "%s_%04d.bin" % (opt["name"], kept)
            open(os.path.join(opt["out"], name), "wb").write(data)
            m = md.ROW_RE.match(last)
            x, y = int(m.group(2), 16) >> 8, (int(m.group(3), 16) >> 8) & 0xff
            index.write(f"{name} records {len(data)} step {g} x {x} Y {y} {m.group(6)} slots {slots}\n"); index.flush()
            kept += 1
            if kept >= opt["max"]: break
        print(f"tried {tried} reached {reached} kept {kept} rejected {rejected}", flush=True)
    for f in os.listdir(tmp): os.remove(os.path.join(tmp, f))
    os.rmdir(tmp)
    print(f"done: {kept} prefixes in {opt['out']} ({opt['name']}.txt); tried {tried}, reached {reached}, rejected {rejected}")

if __name__ == "__main__":
    main()
