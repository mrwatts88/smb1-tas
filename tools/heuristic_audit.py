#!/usr/bin/env python3
"""P1.3 — audit MrWint's XPos bound (the x lower bound every search prunes with) against the real game.

For random-input trajectories in the 1-1 third room (the WR's records up to ROOT, then random A/B/L/R
records), the QuickNES core (build/harness) gives the true x per frame, and `smb-opt trace11bound` gives,
for the model state after every step (difftest-verified equal to the core's), the table's maximum x gain in
1..40 further steps — exactly the quantity the search uses to prune. The audit asserts, for every step t and
every k, core_x(t+k) - core_x(t) <= bound_k(t), and reports violations, unknown classes ('?', which the search
treats as "never prune"), and how tight the bound is. Trajectories stop at a death, a grab, or any non-Success
model result. Units: x_pos (256 = 1 px). Alignment (F45/F53): model step i from record 1048 = core frame 1046+i.

Usage: tools/heuristic_audit.py [--n 50] [--len 150] [--seed 1] [--root-record 1048] [--batch 25]
  [--pr PR --pl PL --pa PA --pb PB] [--keep DIR]
"""
import os, random, re, subprocess, sys, tempfile

CORE = "third_party/QuickNES_Core/quicknes_libretro.so"
ROM = "roms/Super Mario Bros. (W) [!].nes"
HARNESS = "build/harness"
SMBOPT = "third_party/smb-opt/target/release/smb-opt"
WR = "data/wr/wr_inputs.bin"
MODEL_FIRST = 1048
MODEL_FRAME0 = 1046
A, B, L, R = 0x01, 0x02, 0x40, 0x80
XPAGE, XPX, XSUB, GES = 0x6D, 0x86, 0x0400, 0x0E
ROW_RE = re.compile(r"^(\d+) (0x[0-9a-f]+) (0x[0-9a-f]+) (0x[0-9a-f]+) (0x[0-9a-f]+) (\w+) .* (Success.*|StateChange.*|HitVine.*|Invalid.*)$")

def run_core(inputs_path, ram_path):
    frames = len(open(inputs_path, "rb").read()) - 2
    subprocess.run([HARNESS, CORE, ROM, inputs_path, "--input-skip", "2", "--frames", str(frames),
                    "--ram", ram_path, "--quiet"], check=True, stdout=subprocess.DEVNULL)
    data = open(ram_path, "rb").read()
    assert len(data) == frames * 2048
    xs, ges = [], []
    for f in range(frames):
        o = f * 2048
        xs.append(((data[o + XPAGE] << 8 | data[o + XPX]) << 8) | data[o + XSUB])
        ges.append(data[o + GES])
    return xs, ges

def run_model(paths, steps):
    out = subprocess.run([SMBOPT, "trace11bound", str(MODEL_FIRST), str(steps)] + paths, check=True, capture_output=True, text=True).stdout
    traces, cur, last = {}, None, None
    for line in out.splitlines():
        if line.startswith("=== "):
            cur = line[4:]; traces[cur] = {}; last = None
            continue
        if line.startswith("bounds: ") and last is not None:
            traces[cur][last]["bounds"] = [None if t == "?" else int(t) for t in line[8:].split()]
            continue
        m = ROW_RE.match(line)
        if m and cur is not None:
            step = int(m.group(1)); last = step
            traces[cur][step] = dict(x=int(m.group(2), 16), result=m.group(7), death=line.rstrip().endswith("DEATH"))
    return traces

def main():
    opt = dict(n=50, len=150, seed=1, root=1048, batch=25, pr=.75, pl=.15, pa=.25, pb=.6, keep=None)
    args = sys.argv[1:]; i = 0
    while i < len(args):
        a = args[i]
        if a == "--root-record": opt["root"] = int(args[i + 1]); i += 2
        elif a == "--keep": opt["keep"] = args[i + 1]; i += 2
        elif a.startswith("--") and a[2:] in opt:
            v = args[i + 1]; opt[a[2:]] = float(v) if "." in v else int(v); i += 2
        else: raise SystemExit(f"unknown option {a}")
    wr = open(WR, "rb").read()
    rng = random.Random(opt["seed"])
    tmp = opt["keep"] or tempfile.mkdtemp(prefix="haudit_")
    os.makedirs(tmp, exist_ok=True)
    paths = []
    for t in range(opt["n"]):
        rnd = bytes((R if rng.random() < opt["pr"] else 0) | (L if rng.random() < opt["pl"] else 0)
                    | (A if rng.random() < opt["pa"] else 0) | (B if rng.random() < opt["pb"] else 0) for _ in range(opt["len"]))
        p = os.path.join(tmp, f"t{t}.bin"); open(p, "wb").write(wr[: opt["root"]] + rnd); paths.append(p)
    steps = opt["root"] + opt["len"] - MODEL_FIRST
    checks = viol = unknown = 0; worst = 0.0; worst_at = None; steps_total = 0; tight = [0, 0]
    for b in range(0, len(paths), opt["batch"]):
        batch = paths[b: b + opt["batch"]]
        traces = run_model(batch, steps)
        for p in batch:
            xs, ges = run_core(p, p + ".ram")
            tr = traces[p]
            # stop at the first non-Success / death; the core must also still be in control (GES 8)
            end = steps
            for s in range(steps):
                if s not in tr or tr[s]["result"] != "Success" or tr[s]["death"]:
                    end = s; break
            for s in range(end):
                f = MODEL_FRAME0 + s
                if f >= len(xs) or xs[f] != tr[s]["x"]:
                    raise SystemExit(f"{p}: model/core x mismatch at step {s}: model {tr[s]['x']:#x} core {xs[f]:#x}")
                steps_total += 1
                bounds = tr[s].get("bounds")
                if bounds is None or bounds[0] is None:
                    unknown += 1; continue
                for k in range(1, 41):
                    if s + k >= end or f + k >= len(xs) or ges[f + k] != 8:
                        break
                    gain = xs[f + k] - xs[f]
                    checks += 1
                    if gain > bounds[k - 1]:
                        viol += 1
                        if viol <= 20:
                            print(f"VIOLATION {p} step {s} (frame {f}) k={k}: gain {gain} > bound {bounds[k-1]}")
                    if bounds[k - 1] > 0:
                        r = gain / bounds[k - 1]
                        if r > worst: worst, worst_at = r, (p, s, k, gain, bounds[k - 1])
                        if gain == bounds[k - 1]: tight[0] += 1
                        tight[1] += 1
            os.remove(p + ".ram")
    print(f"trials {opt['n']} len {opt['len']} root {opt['root']} seed {opt['seed']}: {steps_total} steps, {checks} (step,k) checks, "
          f"{viol} violations, {unknown} steps with an unknown class; bound attained exactly in {tight[0]}/{tight[1]} checks; "
          f"max gain/bound ratio {worst:.4f} at {worst_at}")
    if not opt["keep"]:
        for p in paths: os.remove(p)
        os.rmdir(tmp)

if __name__ == "__main__":
    main()
