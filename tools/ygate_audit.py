#!/usr/bin/env python3
"""P2.3c-2c — audit the y-coupled position-goal bound (smb-opt `ygate`, `bfscx --goal-x GX --goal-y GY`) in the model.

For random (or mutated) input trajectories from a case's root, `smb-opt traceh` prints per step the model state,
the bound h(state) = lower bound on the steps until `x_pos >= GX && Player_Y <= GY` hold at the same step, and
whether they hold. The audit asserts, for every step t whose trajectory later reaches the goal at t' (the first
goal step > t): t' - t >= h(t). It reports violations, how many trajectories reached the goal, how tight h was
(min/mean of t' - t - h at the steps with a later goal) and the h distribution, so a bound that is sound but
useless shows up as loose rather than silently passing.

The random inputs are right-biased with A held in runs (jumps of random length) and B mostly held (running), so
the trajectories climb, hop over the pits and reach the goal region; `--mutate FILE K PM` instead takes the K
records of FILE from --first (a known goal path, e.g. a bfscx-path result) and flips each record's bits with
probability PM — trajectories close to the optimum, where the bound is tightest and an unsound term bites.
Model alignment/semantics as in tools/model_difftest.py --case.

Usage: tools/ygate_audit.py --case W42Main --first 6584 --gx 339 --gy 112 [--lift 0] [--n 200] [--len 220]
  [--seed 1] [--pr .85 --pl .05 --pa .2 --amax 30 --pb .8] [--mutate FILE K PM] [--batch 50] [--keep DIR] [--verbose]
"""
import os, random, re, subprocess, sys, tempfile

SMBOPT = "third_party/smb-opt/target/release/smb-opt"
WR = "data/wr/wr_inputs.bin"
A, B, L, R = 0x01, 0x02, 0x40, 0x80
ROW_RE = re.compile(r"^(\d+) (0x[0-9a-f]+) (0x[0-9a-f]+) (0x[0-9a-f]+) (0x[0-9a-f]+) (\w+) (\d+|\?) ([01]) (\S+)")


def gen_random(rng, n, pr, pl, pa, amax, pb):
    out = []
    a_left = 0
    for _ in range(n):
        v = 0
        u = rng.random()
        if u < pr: v |= R
        elif u < pr + pl: v |= L
        if a_left > 0: a_left -= 1; v |= A
        elif rng.random() < pa: a_left = rng.randint(0, amax); v |= A
        if rng.random() < pb: v |= B
        out.append(v)
    return bytes(out)


def gen_mutate(rng, base, pm):
    out = bytearray(base)
    for i in range(len(out)):
        if rng.random() < pm:
            out[i] ^= rng.choice([A, B, L, R, A | B, L | R])
    return bytes(out)


def run_traces(case, paths, first, n, lift, gx, gy):
    """One traceh process over many input files -> {path: rows}."""
    cmd = [SMBOPT, "traceh", case, str(first), str(n)]
    if lift is not None: cmd += ["--lift", str(lift)]
    cmd += ["--goal-x", str(gx), "--goal-y", str(gy)] + paths
    out = subprocess.run(cmd, check=True, capture_output=True, text=True).stdout
    traces, cur = {}, None
    for line in out.splitlines():
        if line.startswith("=== "):
            cur = line[4:]; traces[cur] = []
            continue
        m = ROW_RE.match(line)
        if m and cur is not None:
            traces[cur].append(dict(step=int(m.group(1)), x=int(m.group(2), 16), y=int(m.group(3), 16),
                                    state=m.group(6), h=None if m.group(7) == "?" else int(m.group(7)),
                                    goal=m.group(8) == "1", result=m.group(9)))
    return traces


def main():
    opt = dict(case="W42Main", first=6584, gx=None, gy=None, lift=None, n=200, len=220, seed=1,
               pr=.85, pl=.05, pa=.2, amax=30, pb=.8, mutate=None, keep=None, verbose=False, batch=50)
    args = sys.argv[1:]; i = 0
    while i < len(args):
        k = args[i].lstrip("-")
        if k == "verbose": opt[k] = True; i += 1; continue
        if k == "mutate": opt[k] = (args[i + 1], int(args[i + 2]), float(args[i + 3])); i += 4; continue
        v = args[i + 1]
        if k in ("case", "keep"): opt[k] = v
        elif k in ("pr", "pl", "pa", "pb"): opt[k] = float(v)
        else: opt[k] = int(v)
        i += 2
    assert opt["gx"] is not None and opt["gy"] is not None, "--gx and --gy are required"
    rng = random.Random(opt["seed"])
    wr = open(WR, "rb").read()
    prefix = wr[:opt["first"]]
    base = None
    if opt["mutate"]:
        path, k, pm = opt["mutate"]
        d = open(path, "rb").read()
        base = d[opt["first"]:opt["first"] + k] if len(d) > opt["first"] + k - 1 else d[:k]
        assert len(base) == k, "mutation base too short"
    tmpdir = opt["keep"] or tempfile.mkdtemp(prefix="ygate_audit_")
    os.makedirs(tmpdir, exist_ok=True)
    viol, checks, reached, slack_sum, slack_min = 0, 0, 0, 0, None
    hmax, hist = 0, {}
    never_but_reached = 0
    paths = []
    for t in range(opt["n"]):
        if base is not None:
            rec = gen_mutate(rng, base, opt["mutate"][2])
            if len(rec) < opt["len"]: rec += gen_random(rng, opt["len"] - len(rec), opt["pr"], opt["pl"], opt["pa"], opt["amax"], opt["pb"])
        else:
            rec = gen_random(rng, opt["len"], opt["pr"], opt["pl"], opt["pa"], opt["amax"], opt["pb"])
        p = os.path.join(tmpdir, "trial_%04d.bin" % t)
        open(p, "wb").write(prefix + rec)
        paths.append(p)
    traces = {}
    for b in range(0, len(paths), opt["batch"]):
        traces.update(run_traces(opt["case"], paths[b:b + opt["batch"]], opt["first"], opt["len"], opt["lift"], opt["gx"], opt["gy"]))
    for t, p in enumerate(paths):
        rows = traces.get(p, [])
        goal_steps = [r["step"] for r in rows if r["goal"]]
        if goal_steps: reached += 1
        for r in rows:
            if r["h"] is None: continue
            hmax = max(hmax, r["h"]); hist[r["h"]] = hist.get(r["h"], 0) + 1
            if r["goal"]: continue
            later = [g for g in goal_steps if g > r["step"]]
            if not later: continue
            tp = later[0]
            checks += 1
            s = tp - r["step"] - r["h"]
            if r["h"] >= 0x7ff0: never_but_reached += 1
            if s < 0:
                viol += 1
                print("VIOLATION trial %d step %d: h %d but goal at step %d (%d later) x %.2f Y %.2f %s file %s" % (
                    t, r["step"], r["h"], tp, tp - r["step"], r["x"] / 256, r["y"] / 256 - 256, r["state"], p))
            else:
                slack_sum += s; slack_min = s if slack_min is None else min(slack_min, s)
        if opt["verbose"]:
            print("trial %d: %d rows, goal steps %s, last %s" % (t, len(rows), goal_steps[:3], rows[-1]["result"] if rows else "-"))
        if not opt["keep"]: os.remove(p)
    print("trials %d, reached the goal %d, admissibility checks %d, violations %d (never-bound on a goal path: %d)" % (
        opt["n"], reached, checks, viol, never_but_reached))
    if checks:
        print("slack t'-t-h: min %d, mean %.2f over %d checks" % (slack_min, slack_sum / max(1, checks - viol), checks))
    print("h max %d; h histogram (h: count): %s" % (hmax, " ".join("%d:%d" % kv for kv in sorted(hist.items())[:40])))
    if not opt["keep"]:
        try: os.rmdir(tmpdir)
        except OSError: pass
    return 1 if viol else 0


if __name__ == "__main__":
    sys.exit(main())
