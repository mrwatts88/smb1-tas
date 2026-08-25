#!/usr/bin/env python3
"""Frame-by-frame AreaParserTaskNum / CoinTally equality between a smb-opt case model and the fceux core.

This is the control that block-state work must pass: the field difftest (x/y/speeds) is blind to the parser,
so a model can match Mario exactly for a whole level while running the area parser a frame off — which moves
every piranha-plant spawn (F147/F148/F149).

Model step k is the state after applying input record FIRST+k, i.e. fm2 frame FIRST+1+k, i.e. RAM row
FIRST+2+k (tools/ram_trace.py: row i = frame i-1).

Coins: only coin **metatiles** ($c2, AwardTouchedCoin / CheckTopOfBlock) are compared, because only those
reach VRAM through RemoveCoin_Axe and set VRAM_Buffer_AddrCtrl = 6. `CoinBlock` — bumping a $c0/$5f/$58/$5d
block whose contents is a coin — calls GiveOneCoin without RemoveCoin_Axe, so it moves CoinTally but cannot
stall the parser and the model deliberately does not track it. Pass --no-coins for a case with such blocks
on its route (4-2 has a $c0 at column 51).

Usage: tools/parser_check.py CASE INPUTS.bin FIRST N [RAMFILE] [--enemies] [--no-coins] [--max-report=M]
Example: tools/parser_check.py W12Warp data/wr/wr_inputs.bin 2486 1280
"""
import subprocess
import sys

SMBOPT = "third_party/smb-opt/target/release/smb-opt"
APTN, TALLY, SL, SLOCK = 0x071F, 0x075E, 0x071C, 0x0723


def main():
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    case, inputs, first, n = a[0], a[1], int(a[2]), int(a[3])
    ram = a[4] if len(a) > 4 else "data/wr/fceux_wr.ram"
    enemies = "--enemies" in sys.argv
    no_coins = "--no-coins" in sys.argv
    maxrep = next((int(x.split("=")[1]) for x in sys.argv if x.startswith("--max-report=")), 20)

    cmd = [SMBOPT, "tracec", case, inputs, str(first), str(n)] + (["--enemies"] if enemies else [])
    out = subprocess.run(cmd, capture_output=True, text=True).stdout
    model = []          # [aptn, coins, sl, lock] after each step; replayce prints scroll: before blocks:
    pending_sl = None
    for ln in out.split("\n"):
        f = ln.split()
        if ln.startswith("scroll:"):
            pending_sl = int(f[1])
        elif ln.startswith("blocks:"):
            model.append([int(f[f.index("aptn") + 1]), None, pending_sl, None])
            pending_sl = None
        elif ln.startswith("coins:") and model:
            model[-1][1] = bin(int(f[1], 0)).count("1")
            if "slock" in f:
                model[-1][3] = f[f.index("slock") + 1] == "true"
    if not model:
        raise SystemExit("no blocks: lines — is BlockStates ON for this case?")

    d = open(ram, "rb").read()
    bad = 0
    coin0 = None
    for k, (aptn, coins, sl, lock) in enumerate(model):
        m = d[(first + 1 + k) * 2048:(first + 2 + k) * 2048]
        if not m:
            print(f"ram exhausted at step {k}")
            break
        core_aptn, core_tally = m[APTN], m[TALLY]
        if coin0 is None:
            coin0 = core_tally - (coins or 0)
        ok_a = aptn == core_aptn
        ok_c = no_coins or coins is None or coins + coin0 == core_tally
        ok_s = sl is None or sl == m[SL]
        ok_l = lock is None or lock == (m[SLOCK] != 0)
        if not (ok_a and ok_c and ok_s and ok_l):
            bad += 1
            if bad <= maxrep:
                print(f"  step {k:5d} (row {first+2+k})  aptn model {aptn} core {core_aptn}"
                      f"   coins model {coins} core {core_tally - coin0}"
                      f"   sl model {sl} core {m[SL]}   lock model {lock} core {m[SLOCK] != 0}")
    print(f"{case}: {len(model)} steps, {len(model)-bad} equal, {bad} MISMATCH")
    return 1 if bad else 0


sys.exit(main())
