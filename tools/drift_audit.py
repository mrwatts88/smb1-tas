#!/usr/bin/env python3
"""P2.3c-5 — audit the scroll-aware drift bound (smb-opt heuristics::drift, `bfscx --enemies` on W42Main's case goal).

The bound h(s) is the BFS distance in a relaxed graph (x, Player_Y, scroll offset, side-collision credit) to the
wrong-warp pipe entry with ScreenLeft <= 1216. It is admissible iff every model transition of a surviving state maps
to a relaxed transition of cost 1, which this audit tests directly as CONSISTENCY along model trajectories under the
search hook: for every step s -> s' that the search would keep (no death, no refusal), h(s) <= h(s') + 1, and h = 0 at
a goal. (The trajectories need not reach the goal — the finale needs a full 20-px drift — so the ygate-style
"t' - t >= h(t)" test is not available; consistency + h(goal) = 0 implies admissibility for a graph distance.)

Trajectories: the chained prefix (e.g. runs/P2.3c-2c/chain_s4v3.bin, 6584 + 509 records: the vine-bumped chain on
pipe B's top) plus random suffixes in phases (run right / wall play with Left, Left+A, Right, idle) so the
trajectories reach the relative-112 wall, bump the bricks and the pipe faces, and sometimes mint offset (rows with
rel > 112 are counted — the audit is only meaningful if minting was exercised). Optionally the WR's own inputs
from 6584 (its wall walk is left of the bound's domain; its finale runs the m >= 20 region).

Usage: tools/drift_audit.py [--prefix runs/P2.3c-2c/chain_s4v3.bin --first 6584 --plen 509] [--n 400] [--len 90]
  [--seed 1] [--batch 40] [--wr] [--keep DIR] [--verbose]
"""
import argparse, os, random, re, subprocess, sys, tempfile

SMBOPT = "third_party/smb-opt/target/release/smb-opt"
WR = "data/wr/wr_inputs.bin"
A, B, L, R = 0x01, 0x02, 0x40, 0x80
ROW_RE = re.compile(r"^(\d+) (0x[0-9a-f]+) (0x[0-9a-f]+) (0x[0-9a-f]+) (0x[0-9a-f]+) (\w+) (\d+|\?) ([01]) (\S+)(.*)$")


def gen_phased(rng, n):
    """Right-biased running with random jumps, interleaved with 'wall play' phases (Left / Left+A / idle / Right)."""
    out = []
    i = 0
    while i < n:
        phase = rng.random()
        k = rng.randint(3, 25)
        if phase < 0.45:   # run right, random A runs
            a_left = 0
            for _ in range(k):
                v = R | (B if rng.random() < 0.85 else 0)
                if a_left > 0: a_left -= 1; v |= A
                elif rng.random() < 0.15: a_left = rng.randint(0, 25); v |= A
                out.append(v)
        elif phase < 0.75: # wall play: mostly Left, sometimes A, sometimes nothing
            for _ in range(k):
                u = rng.random()
                v = L if u < 0.6 else (L | A if u < 0.75 else (0 if u < 0.9 else R))
                if rng.random() < 0.3: v |= B
                out.append(v)
        elif phase < 0.9:  # hop right / left
            v = (R if rng.random() < 0.7 else L) | A | (B if rng.random() < 0.5 else 0)
            for _ in range(k): out.append(v)
        else:              # idle / crouch
            for _ in range(k): out.append(rng.choice([0, 0, L | R, B]))
        i += k
    return bytes(out[:n])


def run_traces(paths, first, n, enemies=0):
    cmd = [SMBOPT, "traceh", "W42Main", str(first), str(n), "--enemies", str(enemies)] + paths
    out = subprocess.run(cmd, check=True, capture_output=True, text=True).stdout
    traces, cur, note = {}, None, []
    for line in out.splitlines():
        if line.startswith("=== "): cur = line[4:]; traces[cur] = []; continue
        m = ROW_RE.match(line)
        if m and cur is not None:
            step, xp, yp, xs, ys, st, h, goal, res, tail = m.groups()
            traces[cur].append(dict(step=int(step), x=int(xp, 16), y=int(yp, 16), h=None if h == "?" else int(h), goal=goal == "1", res=res,
                                    dead=" DEAD" in tail, bump=" ITEMBUMP" in tail, rel=_tail(tail, "rel"), t=_tail(tail, "t")))
        elif cur is None: note.append(line)
    return traces, note


def _tail(tail, key):
    m = re.search(r"\b" + key + r" (-?\d+)", tail)
    return int(m.group(1)) if m else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prefix", default="runs/P2.3c-2c/chain_s4v3.bin"); ap.add_argument("--first", type=int, default=6584); ap.add_argument("--plen", type=int, default=509)
    ap.add_argument("--n", type=int, default=400); ap.add_argument("--len", type=int, default=90); ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--batch", type=int, default=40); ap.add_argument("--wr", action="store_true"); ap.add_argument("--keep"); ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()
    rng = random.Random(args.seed)
    prefix = open(args.prefix, "rb").read()
    base = prefix[: args.first + args.plen]
    assert len(base) == args.first + args.plen, "prefix file shorter than first + plen"
    tmp = args.keep or tempfile.mkdtemp(prefix="drift_audit_")
    os.makedirs(tmp, exist_ok=True)
    files = []
    for i in range(args.n):
        p = os.path.join(tmp, "t%04d.bin" % i)
        open(p, "wb").write(base + gen_phased(rng, args.len))
        files.append((p, args.first, args.plen + args.len))
    if args.wr: files.append((WR, 6584, 600))
    pairs = viol = goals = rows = minted_rows = 0
    max_rel = 0; max_h = 0; inf_rows = 0; live_rows = 0; hist = {}
    first_viol = []
    by_first = {}
    for p, f, n in files: by_first.setdefault((f, n), []).append(p)
    note_printed = False
    for (f, n), paths in by_first.items():
        for b in range(0, len(paths), args.batch):
            traces, note = run_traces(paths[b : b + args.batch], f, n)
            if not note_printed:
                for l in note:
                    if "drift bound" in l or "credit" in l: print(l)
                note_printed = True
            for path, rws in traces.items():
                rows += len(rws)
                for i, r in enumerate(rws):
                    if r["rel"] is not None: max_rel = max(max_rel, r["rel"]); minted_rows += r["rel"] > 112
                    if r["h"] is not None:
                        if r["h"] >= 1000: inf_rows += 1
                        else: max_h = max(max_h, r["h"])
                        if r["x"] >> 8 >= 1180 and r["h"] < 1000: live_rows += 1; hist[r["h"]] = hist.get(r["h"], 0) + 1
                    if r["goal"]:
                        goals += 1
                        if r["h"] != 0: viol += 1; first_viol.append((path, r["step"], "goal with h %s" % r["h"]))
                    if i + 1 < len(rws):
                        s2 = rws[i + 1]
                        if s2["dead"] or s2["bump"]: continue  # the child is pruned by the search: no constraint
                        if r["h"] is None or s2["h"] is None: continue
                        pairs += 1
                        if r["h"] > s2["h"] + 1:
                            viol += 1
                            if len(first_viol) < 20: first_viol.append((path, r["step"], "h %d -> %d (x %d->%d Y %d->%d rel %s->%s t %s->%s)" % (r["h"], s2["h"], r["x"] >> 8, s2["x"] >> 8, (r["y"] >> 8) - 256, (s2["y"] >> 8) - 256, r["rel"], s2["rel"], r["t"], s2["t"])))
    print("trajectories %d (+WR %s), rows %d, consistency pairs %d, VIOLATIONS %d, goals %d" % (args.n, args.wr, rows, pairs, viol, goals))
    print("minting exercised: rows with rel > 112: %d (max rel %d); rows in the bound's domain with finite h: %d, h = INF rows: %d, max finite h %d" % (minted_rows, max_rel, live_rows, inf_rows, max_h))
    if hist:
        ks = sorted(hist); print("h histogram (domain rows):", " ".join("%d:%d" % (k, hist[k]) for k in ks))
    for v in first_viol[:20]: print("  VIOLATION", v)
    if not args.keep:
        for p, _, _ in files:
            if p != WR: os.remove(p)
        os.rmdir(tmp)
    sys.exit(1 if viol else 0)


if __name__ == "__main__":
    main()
