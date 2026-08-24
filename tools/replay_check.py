#!/usr/bin/env python3
"""Replay a search result on the QuickNES core and the model (P2.3c-1): inputs = the WR's records up to
FIRST+PREFIX, then the NES-order bytes of PATH (e.g. written by `smb-opt bfscx-path … --out`), optionally with
Down added to the last record (a vertical pipe entry needs Down, F74). Compares the core and the model frame by
frame with tools/model_difftest.py's machinery and reports the goal (core GES 3 = pipe entry) frame.

Usage: tools/replay_check.py --case CASE --first R --prefix N --path FILE [--lift APTN0 | --enemies APTN0] [--down] [--extra K] [--verbose]
  --enemies APTN0   W42Main with the lift + enemy module (P2.5c-2): the model's stomps must coincide with the core's;
                    required to verify any chain carrying enemy events (e.g. the 4-2 top route's 2 stomps).
  --extra K   append K more of the WR's own records after PATH (to see what follows)
Example: tools/replay_check.py --case W42Main --first 6584 --prefix 575 --path runs/P2.3c/ctrl_w42main_path.bin --lift 0 --down
"""
import os, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import model_difftest as md

def main():
    args = sys.argv[1:]
    opt = dict(lift=None, enemies=None, down=False, extra=0, verbose=False)
    i = 0
    while i < len(args):
        a = args[i]
        if a in ("--case", "--path"): opt[a[2:]] = args[i + 1]; i += 2
        elif a in ("--first", "--prefix", "--lift", "--enemies", "--extra"): opt[a[2:]] = int(args[i + 1]); i += 2
        elif a == "--down": opt["down"] = True; i += 1
        elif a == "--verbose": opt["verbose"] = True; i += 1
        else: raise SystemExit(f"unknown option {a}")
    md.CASE = opt["case"]; md.MODEL_FIRST = opt["first"]; md.MODEL_FRAME0 = opt["first"] - 2; md.LIFT = opt["lift"]; md.ENEMIES = opt["enemies"]
    wr = open(md.WR, "rb").read()
    path = bytearray(open(opt["path"], "rb").read())
    if opt["down"]: path[-1] |= 0x20
    root = opt["first"] + opt["prefix"]
    inputs = wr[:root] + bytes(path) + wr[root + len(path): root + len(path) + opt["extra"]]
    tmp = tempfile.mkdtemp(prefix="replay_")
    ip = os.path.join(tmp, "inputs.bin"); open(ip, "wb").write(inputs)
    first_step = opt["prefix"]; last_step = first_step + len(path) + opt["extra"] - 1
    frames = md.MODEL_FRAME0 + last_step + 1
    core = md.run_core(ip, frames, os.path.join(tmp, "inputs.ram"))
    model = md.run_model(ip, last_step + 1)
    n, mism, grab, ev = md.compare(core, model, first_step, last_step, opt["verbose"])
    etxt = (f"; stomps {ev['stomps']}, kicks {ev['kicks']}" if md.ENEMIES is not None else "")
    print(f"compared {n} frames from record {root} (QuickNES frame {md.MODEL_FRAME0 + first_step}); mismatches: {len(mism)}{etxt}")
    for f, k, m, c in mism[:10]: print(f"  frame {f} {k}: model {m} core {c}")
    if grab: print("goal:", grab)
    # core-side pipe entry: first frame with GES 3 in the replayed window
    ges3 = [f for f in range(md.MODEL_FRAME0 + first_step, frames) if md.core_row(core, f)["GES"] == 3]
    print("core pipe entry (GES 3) frame:", ges3[0] if ges3 else None, "= record", ges3[0] + 2 if ges3 else None)
    os.remove(ip); os.remove(os.path.join(tmp, "inputs.ram")); os.rmdir(tmp)

if __name__ == "__main__":
    main()
