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
  --enemies APTN0   W42Main with the lift + enemy module (P2.5c-2): model deaths must coincide with the core's GES 11;
                    stomps/kicks are counted from the model's trace and the player fields after them are compared
                    as usual; a bump of an item cell ((28,7) (55,7) (81,7) (64,3), H34: unmodelled spawns) stops
                    the trial on that frame without a verdict (like a pit), reported as "item bump".
  --arun AMAX       A held in runs of random length 0..AMAX (jumps of every height), started with probability pa
  --wr-file FILE    use FILE's records as "the WR" (--wr compares FILE's own records from --root-record: a frame-by-
                    frame check of a prefix file); --only SUBSTR runs only the trials whose name contains SUBSTR
                    (the random stream is unchanged, so a trial of a big run is reproduced exactly; use --keep DIR)
  --stop-x X        stop a trial without a verdict once the model's X >= X (W42Main: 1540 = the last columns of the
                    block map, cols 0-97; beyond it the model has no blocks and no verdict is meaningful)
  --require-event   run the model first and spend a core run only on trials whose model trace has a Stomp/Kick
                    (stomp/kick-dense difftests from a large random pool; skipped trials are counted)
  --prefix FILE     the trial prefix = FILE's records (instead of the WR's records up to --root-record); the random
                    records follow it. --prefix-dir DIR: every *.bin in DIR (sorted) is used as a prefix, --n trials
                    each (tools/w42_prefix_gen.py writes such prefixes: enemy-dense difftests from a chosen region).
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
ITEM_MASK = (1 << 3) | (1 << 7) | (1 << 11) | (1 << 15)   # W42MainBlocks::CELLS bits of (64,3) (28,7) (55,7) (81,7)
BLOCKS_RE = re.compile(r"^blocks: bounce \d+ used (0x[0-9a-f]+|\d+) ")

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
    step = None
    for line in out.splitlines():
        m = ROW_RE.match(line)
        if not m:
            if line and line[0].isdigit():
                raise SystemExit(f"unparsed model row: {line!r}")
            b = BLOCKS_RE.match(line)
            if b and step is not None:
                rows[step]["USED"] = int(b.group(1), 0)
            continue
        step = int(m.group(1))
        x_pos, y_pos, x_spd, y_spd = (int(m.group(k), 16) for k in (2, 3, 4, 5))
        x_spd, y_spd = s16(x_spd & 0xffff), s16(y_spd & 0xffff)
        rows[step] = dict(XP=(x_pos >> 8) & 0xffff, XSUB=x_pos & 0xff, XSPD=x_spd >> 8, XFRAC=x_spd & 0xff,
                          YP=(y_pos >> 8) & 0xffff, YSPD=y_spd >> 8, YFRAC=y_spd & 0xff,
                          STATE=STATES[m.group(6)], RESULT=m.group(10), USED=0)
    return rows

STOP_X = None               # --stop-x: stop without verdict when the model's X reaches it (e.g. the end of a case's block map)

D = 0x20                    # NES Down

def compare(core, model, first_step, last_step, verbose, inputs=None):
    """Returns (frames_compared, mismatches[(frame, field, model, core)], grab_info, events{stomps, kicks})."""
    mism, n = [], 0
    grab = None
    ev = dict(stomps=0, kicks=0)
    # item bumps already in the prefix are the caller's responsibility (the WR's (28,7) mushroom at ~6780 is
    # harmless for slot occupancy: the object is gone by 6889, before the lift spawns; module check to 7038)
    used0 = model[first_step - 1]["USED"] if first_step > 0 and (first_step - 1) in model else 0
    for step in range(first_step, last_step + 1):
        f = MODEL_FRAME0 + step
        if step not in model:
            break
        mr = model[step]
        cr = core_row(core, f)
        if "STOMP" in mr["RESULT"]: ev["stomps"] += 1
        if "KICK" in mr["RESULT"]: ev["kicks"] += 1
        if "StateChangeVerticalPipe" in mr["RESULT"]:
            # vertical pipe entry: the core sets GES 3 on the same frame (HandlePipeEntry); positions comparable
            grab = dict(model_frame=f, model_y=mr["YP"] & 0xff, core_ges=cr["GES"], core_y=cr["YP"] & 0xff,
                        core_frame=f if cr["GES"] == 3 else None, pipe=True)
            if inputs is not None and not (inputs[MODEL_FIRST + step] & D):
                grab["no_down"] = True   # F74: the model reports the entry as possible; without Down the core stays
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
        if STOP_X is not None and mr["XP"] >= STOP_X:
            grab = dict(model_frame=None, core_frame=f, core_ges=cr["GES"], core_y=cr["YP"] & 0xff, model_y=None, stopx=True)
            n += 1
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
        if ENEMIES is not None and (mr["USED"] & ITEM_MASK & ~used0 or "ITEMBUMP" in mr["RESULT"]):
            # an item cell was bumped: the core spawns a mushroom/star/vine (H34, outside the model) -> stop here
            grab = dict(model_frame=None, core_frame=f, core_ges=cr["GES"], core_y=cr["YP"] & 0xff, model_y=None, item=True)
            break
    return n, mism, grab, ev

def main():
    args = sys.argv[1:]
    opt = dict(n=100, len=120, seed=1, root=1232, wr=False, keep=None, pr=.75, pl=.15, pa=.25, pb=.6, verbose=False, mutate=0, goombas=False, arun=0)
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
        elif a == "--arun": opt["arun"] = int(args[i + 1]); i += 2
        elif a == "--prefix": opt["prefix"] = args[i + 1]; i += 2
        elif a == "--prefix-dir": opt["prefix_dir"] = args[i + 1]; i += 2
        elif a == "--wr-file": opt["wr_file"] = args[i + 1]; i += 2   # compare FILE's own records instead of the WR's
        elif a == "--only": opt["only"] = args[i + 1]; i += 2         # run only the trials whose name contains this
        elif a == "--require-event": opt["require_event"] = True; i += 1   # model first; core only if a Stomp/Kick occurs
        elif a == "--stop-x": opt["stop_x"] = int(args[i + 1]); i += 2     # stop a trial (no verdict) once the model's X >= this
        else: raise SystemExit(f"unknown option {a}")
    global CASE, MODEL_FIRST, MODEL_FRAME0, LIFT, ENEMIES, STOP_X
    if opt.get("stop_x") is not None: STOP_X = opt["stop_x"]
    if opt.get("lift") is not None: LIFT = opt["lift"]
    if opt.get("enemies") is not None: ENEMIES = opt["enemies"]
    if opt.get("case"):
        CASE = opt["case"]
        MODEL_FIRST = opt["first"]
        MODEL_FRAME0 = MODEL_FIRST - 2
        if opt["root"] == 1232: opt["root"] = MODEL_FIRST
    wr = open(opt.get("wr_file") or WR, "rb").read()
    rng = random.Random(opt["seed"])
    tmp = opt["keep"] or tempfile.mkdtemp(prefix="difftest_")
    os.makedirs(tmp, exist_ok=True)
    trials = [("wr", wr[: opt["root"] + opt["len"]])] if opt["wr"] else []
    prefixes = [("", wr[: opt["root"]])]
    if opt.get("prefix"):
        prefixes = [(os.path.basename(opt["prefix"]).rsplit(".", 1)[0] + "/", open(opt["prefix"], "rb").read())]
    elif opt.get("prefix_dir"):
        names = sorted(f for f in os.listdir(opt["prefix_dir"]) if f.endswith(".bin"))
        prefixes = [(f.rsplit(".", 1)[0] + "/", open(os.path.join(opt["prefix_dir"], f), "rb").read()) for f in names]
    if prefixes[0][0]:
        assert opt["mutate"] == 0 and not opt["wr"], "--prefix/--prefix-dir: random trials only"
        assert all(len(p) >= MODEL_FIRST for _, p in prefixes), "a prefix must reach the case's first record"
    for pname, pfx in prefixes:
      for t in range(opt["n"] if opt["mutate"] == 0 else 0):
        if opt["arun"] > 0:
            # --arun AMAX: A is held in runs of random length 0..AMAX started with probability pa (jumps of every height,
            # as tools/ygate_audit.py) so trials climb to the 4-2 top floor (P2.5c-2)
            out, a_left = [], 0
            for _ in range(opt["len"]):
                v = (R if rng.random() < opt["pr"] else 0) | (L if rng.random() < opt["pl"] else 0) | (B if rng.random() < opt["pb"] else 0)
                if a_left > 0: a_left -= 1; v |= A
                elif rng.random() < opt["pa"]: a_left = rng.randint(0, opt["arun"]); v |= A
                out.append(v)
            rnd = bytes(out)
        else:
            rnd = bytes((R if rng.random() < opt["pr"] else 0) | (L if rng.random() < opt["pl"] else 0)
                        | (A if rng.random() < opt["pa"] else 0) | (B if rng.random() < opt["pb"] else 0)
                        for _ in range(opt["len"]))
        trials.append((f"{pname}t{t}", pfx + rnd))
    for t in range(opt["n"] if opt["mutate"] > 0 else 0):
        # the WR's own records from the root, with `mutate` random frames replaced by random A/B/L/R bytes
        suffix = bytearray(wr[opt["root"]: opt["root"] + opt["len"]])
        for _ in range(opt["mutate"]):
            suffix[rng.randrange(len(suffix))] = rng.choice([0, R, R | B, R | A | B, L, L | R, A, A | R, 0, R | B])
        trials.append((f"m{t}", wr[: opt["root"]] + bytes(suffix)))
    tot_frames, bad, grabs, grab_match = 0, 0, 0, 0
    fpg_n = [0]
    deaths = [0]
    stomps, kicks, items, skipped, nodown = 0, 0, 0, 0, 0
    if opt.get("only"):
        trials = [(nm, inp) for nm, inp in trials if opt["only"] in nm]   # the rng stream is unchanged
    for name, inputs in trials:
        first_step = len(inputs) - opt["len"] - MODEL_FIRST       # = root - MODEL_FIRST without a prefix
        last_step = first_step + opt["len"] - 1
        frames = MODEL_FRAME0 + last_step + 1
        ip = os.path.join(tmp, name.replace("/", "_") + ".bin")
        open(ip, "wb").write(inputs)
        model = run_model(ip, last_step + 1, opt["goombas"])
        if opt.get("require_event") and not any(("STOMP" in r["RESULT"] or "KICK" in r["RESULT"]) for st, r in model.items() if st >= first_step):
            skipped += 1
            if not opt["keep"]: os.remove(ip)
            continue
        core = run_core(ip, frames, os.path.join(tmp, name.replace("/", "_") + ".ram"))
        n, mism, grab, ev = compare(core, model, first_step, last_step, opt["verbose"], inputs)
        stomps += ev["stomps"]; kicks += ev["kicks"]
        tot_frames += n
        status = "ok"
        if mism:
            bad += 1
            status = "MISMATCH " + "; ".join(f"f{f} {k} model {m} core {c}" for f, k, m, c in mism[:6])
        gtxt = ""
        if grab:
            if grab.get("pipe") and grab.get("no_down"):
                nodown += 1
                gtxt = f" pipe entry possible at f{grab['model_frame']} Y{grab['model_y']}, no Down pressed (stopped)"
                if grab["model_y"] != grab["core_y"]: bad += 0 if mism else 1; gtxt += " Y DIFF"
            elif grab.get("pipe"):
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
            elif grab.get("stopx"):
                gtxt = f" reached x {STOP_X} at f{grab['core_frame']} (stopped)"
            elif grab.get("item"):
                items += 1
                gtxt = f" item bump at f{grab['core_frame']} (H34, stopped)"
            elif grab.get("death") and grab["death"][0] == grab["death"][1]:
                deaths[0] += 1
                gtxt = f" death f{grab['core_frame']} ok"
            else:
                gtxt = f" core left GES 8 at f{grab['core_frame']} (GES {grab['core_ges']}) vs model death={grab.get('death', (False,))[0]}"
                bad += 0 if mism else 1
        etxt = (f" stomps={ev['stomps']}" if ev["stomps"] else "") + (f" kicks={ev['kicks']}" if ev["kicks"] else "")
        print(f"{name}: {n} frames {status}{gtxt}{etxt}", flush=True)
        if not opt["keep"]:
            os.remove(ip); os.remove(os.path.join(tmp, name.replace("/", "_") + ".ram"))
    print(f"summary: {len(trials)} trials, {tot_frames} frames compared, {bad} trials with a difference, "
          f"{grabs} grabs ({grab_match} identical frame+Y+FPG; {fpg_n[0]} FPG on the core), {deaths[0]} matching deaths"
          + (f", {stomps} stomps, {kicks} kicks, {items} item bumps (stopped)" if ENEMIES is not None else "")
          + (f", {skipped} trials skipped (no model stomp/kick)" if opt.get("require_event") else "")
          + (f", {nodown} pipe entries possible without Down (stopped)" if nodown else ""))
    if not opt["keep"]:
        os.rmdir(tmp)

if __name__ == "__main__":
    main()
