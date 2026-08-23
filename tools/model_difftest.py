#!/usr/bin/env python3
"""Differential test of MrWint's smb-opt player model against the QuickNES core in the 1-1 third room.

Builds input files = the WR's records up to ROOT_RECORD, then random A/B/L/R records (or the WR's own
records with --wr), runs the core (build/harness, RAM dump per frame) and the model (smb-opt trace11pipe
from w11_pipe_start with the goomba bounce injected at step 66, F53) on the same records, and compares per
frame: X (page:pixel), x subpixel ($0400), x speed ($57) and its fraction ($0705), Y (high:pixel), y speed
($9F) and its fraction ($0433), player state ($1D), and the flagpole grab frame + Y (model StateChangeFlag
vs core GameEngineSubroutine == 4).

Alignment (F45/F53): model step i from record 1048 == QuickNES frame 1046+i; harness --input-skip 2 feeds
record j to frame j-2; RAM dump row f = RAM after frame f.

Usage: tools/model_difftest.py [--n 100] [--len 120] [--seed 1] [--root-record 1232] [--wr] [--keep DIR]
  --root-record R   first random record (default 1232 = frame 1230, the root-1229 state of P2.1b)
  --len L           random frames per trial; --n N trials; --seed S
  --wr              single trial with the WR's own records (sanity check: must match everywhere)
  --mutate K        trials = the WR's records from the root with K random frames replaced (FPG-dense)
  --goombas         model = trace11room (goomba pair simulated, no injected bounce); deaths must match GES 11
  --pr PR --pl PL --pa PA --pb PB   per-frame button probabilities (default .75 .15 .25 .6)
  --case NAME --first R  generic segment (P2.3a): model = `smb-opt tracec NAME` from the case's start state with
                    records R.. (model step i == QuickNES frame R-2+i, same law as 1-1); the goal is the case's
                    vertical pipe entry (model StateChangeVerticalPipe vs core GES 3). --root-record defaults to R.
                    E.g. --case W42Warp --first 7247 --wr --len 480 ; --case W42Main --first 6584 --n 50 --len 300
"""
import os, random, re, subprocess, sys, tempfile

CORE = "third_party/QuickNES_Core/quicknes_libretro.so"
ROM = "roms/Super Mario Bros. (W) [!].nes"
HARNESS = "build/harness"
SMBOPT = "third_party/smb-opt/target/release/smb-opt"
WR = "data/wr/wr_inputs.bin"
MODEL_FIRST = 1048          # record index of model step 0 (= QuickNES frame 1046)
MODEL_FRAME0 = 1046
BOUNCE = "66:yspd=-1024"    # goomba stomp at row 1112 (F53)
A, B, L, R = 0x01, 0x02, 0x40, 0x80  # NES order

SYM = dict(X=0x86, PAGE=0x6D, XSUB=0x0400, XSPD=0x57, XFRAC=0x0705, Y=0xCE, YHI=0xB5, YSPD=0x9F,
           YFRAC=0x0433, STATE=0x1D, GES=0x0E)
STATES = {"STANDING": 0, "JUMPING": 1, "FALLING": 2, "CLIMBING": 3}
ROW_RE = re.compile(r"^(\d+) (0x[0-9a-f]+) (0x[0-9a-f]+) (0x[0-9a-f]+) (0x[0-9a-f]+) (\w+) "
                    r"(LEFT \| RIGHT \| LR|LEFT \| RIGHT|LEFT|RIGHT|\(empty\)) (LEFT \| RIGHT \| LR|LEFT \| RIGHT|LEFT|RIGHT|\(empty\)) (.+?) (Success.*|StateChange.*|HitVine.*|Invalid.*)$")

def s16(v):
    return v - 0x10000 if v >= 0x8000 else v

def run_core(inputs_path, frames, ram_path):
    subprocess.run([HARNESS, CORE, ROM, inputs_path, "--input-skip", "2", "--frames", str(frames),
                    "--ram", ram_path, "--quiet"], check=True, stdout=subprocess.DEVNULL)
    data = open(ram_path, "rb").read()
    assert len(data) == frames * 2048, (len(data), frames)
    return data

def core_row(data, f):
    off = f * 2048
    g = lambda a: data[off + a]
    return dict(XP=(g(SYM["PAGE"]) << 8) | g(SYM["X"]), XSUB=g(SYM["XSUB"]),
                XSPD=(g(SYM["XSPD"]) - 256 if g(SYM["XSPD"]) >= 128 else g(SYM["XSPD"])), XFRAC=g(SYM["XFRAC"]),
                YP=(g(SYM["YHI"]) << 8) | g(SYM["Y"]),
                YSPD=(g(SYM["YSPD"]) - 256 if g(SYM["YSPD"]) >= 128 else g(SYM["YSPD"])), YFRAC=g(SYM["YFRAC"]),
                STATE=g(SYM["STATE"]), GES=g(SYM["GES"]))

CASE = None                 # --case NAME: generic tracec mode (MODEL_FIRST/MODEL_FRAME0 set from --first)
LIFT = None                 # --lift APTN0: W42Main with the 4-2 lift hook (tracec ... --lift APTN0)
ENEMIES = None              # --enemies APTN0: W42Main with the lift + enemies hook (P2.5c-2); deaths by enemies must match GES 11

def run_model(inputs_path, steps, goombas=False):
    if CASE:
        cmd = [SMBOPT, "tracec", CASE, inputs_path, str(MODEL_FIRST), str(steps)] + (["--enemies", str(ENEMIES)] if ENEMIES is not None else ["--lift", str(LIFT)] if LIFT is not None else [])
    else:
        cmd = [SMBOPT, "trace11room", inputs_path, str(MODEL_FIRST), str(steps)] if goombas else \
              [SMBOPT, "trace11pipe", inputs_path, str(MODEL_FIRST), str(steps), BOUNCE]
    out = subprocess.run(cmd, check=True, capture_output=True, text=True).stdout
    rows = {}
    for line in out.splitlines():
        m = ROW_RE.match(line)
        if not m:
            if line and line[0].isdigit():
                raise SystemExit(f"unparsed model row: {line!r}")
            continue
        step = int(m.group(1))
        x_pos, y_pos, x_spd, y_spd = (int(m.group(k), 16) for k in (2, 3, 4, 5))
        x_spd, y_spd = s16(x_spd & 0xffff), s16(y_spd & 0xffff)
        rows[step] = dict(XP=(x_pos >> 8) & 0xffff, XSUB=x_pos & 0xff, XSPD=x_spd >> 8, XFRAC=x_spd & 0xff,
                          YP=(y_pos >> 8) & 0xffff, YSPD=y_spd >> 8, YFRAC=y_spd & 0xff,
                          STATE=STATES[m.group(6)], RESULT=m.group(10))
    return rows

def compare(core, model, first_step, last_step, verbose):
    """Returns (frames_compared, mismatches[(frame, field, model, core)], grab_info)."""
    mism, n = [], 0
    grab = None
    for step in range(first_step, last_step + 1):
        f = MODEL_FRAME0 + step
        if step not in model:
            break
        mr = model[step]
        cr = core_row(core, f)
        if "StateChangeVerticalPipe" in mr["RESULT"]:
            # vertical pipe entry: the core sets GES 3 on the same frame (HandlePipeEntry); positions comparable
            grab = dict(model_frame=f, model_y=mr["YP"] & 0xff, core_ges=cr["GES"], core_y=cr["YP"] & 0xff,
                        core_frame=f if cr["GES"] == 3 else None, pipe=True)
            for k in ("XP", "YP"):
                if mr[k] != cr[k]:
                    mism.append((f, k, mr[k], cr[k]))
            n += 1
            break
        if "StateChangeFlag" in mr["RESULT"]:
            # the core sets GES 4 on the grab and, for a glitch grab (Y >= 162), GES 5 in the same frame
            grab = dict(model_frame=f, model_y=mr["YP"] & 0xff, core_ges=cr["GES"], core_y=cr["YP"] & 0xff,
                        core_frame=f if cr["GES"] in (4, 5) else None)
            # position fields are still comparable on the grab frame (x is re-placed on the pole by both)
            for k in ("XP", "YP", "STATE"):
                if mr[k] != cr[k]:
                    mism.append((f, k, mr[k], cr[k]))
            n += 1
            break
        if "DEATH" in mr["RESULT"] or cr["GES"] not in (7, 8):   # GES 7 on the first two control frames
            # model death (goomba contact, trace11room) must coincide with the core's GES 11 (KillPlayer)
            grab = dict(model_frame=None, core_frame=f, core_ges=cr["GES"], core_y=cr["YP"] & 0xff, model_y=None,
                        death=("DEATH" in mr["RESULT"], cr["GES"] == 11))
            n += 1
            for k in ("XP", "YP"):   # KillPlayer rewrites the speeds/state on the death frame; positions must agree
                if mr[k] != cr[k]:
                    mism.append((f, k, mr[k], cr[k]))
            break
        if mr["YP"] >= 0x1d0 or cr["YP"] >= 0x1d0:
            # below the screen bottom (fell into a pit): the game continues in the void until the pit death; not
            # a modeled region (the searches prune y >= 0x1d000 as dead) -> stop here without a verdict
            grab = dict(model_frame=None, core_frame=f, core_ges=cr["GES"], core_y=cr["YP"] & 0xff, model_y=None, pit=True)
            n += 1
            break
        n += 1
        for k in ("XP", "XSUB", "XSPD", "XFRAC", "YP", "YSPD", "YFRAC", "STATE"):
            if mr[k] != cr[k]:
                mism.append((f, k, mr[k], cr[k]))
        if mism and not verbose:
            break
    return n, mism, grab

def main():
    args = sys.argv[1:]
    opt = dict(n=100, len=120, seed=1, root=1232, wr=False, keep=None, pr=.75, pl=.15, pa=.25, pb=.6, verbose=False, mutate=0, goombas=False)
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--n": opt["n"] = int(args[i + 1]); i += 2
        elif a == "--len": opt["len"] = int(args[i + 1]); i += 2
        elif a == "--seed": opt["seed"] = int(args[i + 1]); i += 2
        elif a == "--root-record": opt["root"] = int(args[i + 1]); i += 2
        elif a == "--keep": opt["keep"] = args[i + 1]; i += 2
        elif a in ("--pr", "--pl", "--pa", "--pb"): opt[a[2:]] = float(args[i + 1]); i += 2
        elif a == "--wr": opt["wr"] = True; i += 1
        elif a == "--mutate": opt["mutate"] = int(args[i + 1]); i += 2
        elif a == "--goombas": opt["goombas"] = True; i += 1
        elif a == "--verbose": opt["verbose"] = True; i += 1
        elif a == "--case": opt["case"] = args[i + 1]; i += 2
        elif a == "--first": opt["first"] = int(args[i + 1]); i += 2
        elif a == "--lift": opt["lift"] = int(args[i + 1]); i += 2
        elif a == "--enemies": opt["enemies"] = int(args[i + 1]); i += 2
        else: raise SystemExit(f"unknown option {a}")
    global CASE, MODEL_FIRST, MODEL_FRAME0, LIFT, ENEMIES
    if opt.get("lift") is not None: LIFT = opt["lift"]
    if opt.get("enemies") is not None: ENEMIES = opt["enemies"]
    if opt.get("case"):
        CASE = opt["case"]
        MODEL_FIRST = opt["first"]
        MODEL_FRAME0 = MODEL_FIRST - 2
        if opt["root"] == 1232: opt["root"] = MODEL_FIRST
    wr = open(WR, "rb").read()
    rng = random.Random(opt["seed"])
    tmp = opt["keep"] or tempfile.mkdtemp(prefix="difftest_")
    os.makedirs(tmp, exist_ok=True)
    trials = [("wr", wr[: opt["root"] + opt["len"]])] if opt["wr"] else []
    for t in range(opt["n"] if opt["mutate"] == 0 else 0):
        rnd = bytes((R if rng.random() < opt["pr"] else 0) | (L if rng.random() < opt["pl"] else 0)
                    | (A if rng.random() < opt["pa"] else 0) | (B if rng.random() < opt["pb"] else 0)
                    for _ in range(opt["len"]))
        trials.append((f"t{t}", wr[: opt["root"]] + rnd))
    for t in range(opt["n"] if opt["mutate"] > 0 else 0):
        # the WR's own records from the root, with `mutate` random frames replaced by random A/B/L/R bytes
        suffix = bytearray(wr[opt["root"]: opt["root"] + opt["len"]])
        for _ in range(opt["mutate"]):
            suffix[rng.randrange(len(suffix))] = rng.choice([0, R, R | B, R | A | B, L, L | R, A, A | R, 0, R | B])
        trials.append((f"m{t}", wr[: opt["root"]] + bytes(suffix)))
    first_step = opt["root"] - MODEL_FIRST
    last_step = first_step + opt["len"] - 1
    frames = MODEL_FRAME0 + last_step + 1
    tot_frames, bad, grabs, grab_match = 0, 0, 0, 0
    fpg_n = [0]
    deaths = [0]
    for name, inputs in trials:
        ip = os.path.join(tmp, name + ".bin")
        open(ip, "wb").write(inputs)
        core = run_core(ip, frames, os.path.join(tmp, name + ".ram"))
        model = run_model(ip, last_step + 1, opt["goombas"])
        n, mism, grab = compare(core, model, first_step, last_step, opt["verbose"])
        tot_frames += n
        status = "ok"
        if mism:
            bad += 1
            status = "MISMATCH " + "; ".join(f"f{f} {k} model {m} core {c}" for f, k, m, c in mism[:6])
        gtxt = ""
        if grab:
            if grab.get("pipe"):
                grabs += 1
                ok = grab["core_frame"] == grab["model_frame"] and grab["core_y"] == grab["model_y"]
                grab_match += ok
                gtxt = f" pipe entry model f{grab['model_frame']} Y{grab['model_y']} core GES{grab['core_ges']} Y{grab['core_y']} {'ok' if ok else 'DIFF'}"
                if not ok: bad += 0 if mism else 1
            elif grab.get("model_frame") is not None:
                grabs += 1
                fpg_model = grab["model_y"] >= 162
                fpg_core = grab["core_ges"] == 5
                ok = grab["core_frame"] == grab["model_frame"] and grab["core_y"] == grab["model_y"] and fpg_model == fpg_core
                grab_match += ok
                fpg_n[0] += fpg_core
                gtxt = (f" grab model f{grab['model_frame']} Y{grab['model_y']} fpg={fpg_model} core GES{grab['core_ges']} "
                        f"Y{grab['core_y']} fpg={fpg_core} {'ok' if ok else 'DIFF'}")
                if not ok: bad += 0 if mism else 1
            elif grab.get("pit"):
                gtxt = f" fell below the screen at f{grab['core_frame']} (stopped)"
            elif grab.get("death") and grab["death"][0] == grab["death"][1]:
                deaths[0] += 1
                gtxt = f" death f{grab['core_frame']} ok"
            else:
                gtxt = f" core left GES 8 at f{grab['core_frame']} (GES {grab['core_ges']}) vs model death={grab.get('death', (False,))[0]}"
                bad += 0 if mism else 1
        print(f"{name}: {n} frames {status}{gtxt}")
        if not opt["keep"]:
            os.remove(ip); os.remove(os.path.join(tmp, name + ".ram"))
    print(f"summary: {len(trials)} trials, {tot_frames} frames compared, {bad} trials with a difference, "
          f"{grabs} grabs ({grab_match} identical frame+Y+FPG; {fpg_n[0]} FPG on the core), {deaths[0]} matching deaths")
    if not opt["keep"]:
        os.rmdir(tmp)

if __name__ == "__main__":
    main()
