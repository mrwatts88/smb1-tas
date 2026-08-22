#!/usr/bin/env python3
"""Scan every vertical pipe entry of the WR for a late Down press (P2.3b, F79).

HandlePipeEntry fires on any standing/landing frame with Down held and the feet on the $10/$11 pipe-top tiles
(no speed condition). For each frame where the FCEUX dump's GameEngineSubroutine becomes 3, this replays the WR
on the QuickNES core with Down added to the record 1, 2 and 3 frames earlier (keeping everything else) and reports
the first frame with GES 3. Alignment: FCEUX dump row r carries record r-2; QuickNES frame f carries record f+2
(harness --input-skip 2); GES 3 at dump row r == QuickNES frame r-3.

Usage: tools/pipe_entry_scan.py [--ram data/wr/fceux_wr.ram] [--inputs data/wr/wr_inputs.bin] [--earlier 3]
"""
import os, subprocess, sys, tempfile

CORE = "third_party/QuickNES_Core/quicknes_libretro.so"
ROM = "roms/Super Mario Bros. (W) [!].nes"
HARNESS = "build/harness"
DOWN = 0x20

def ges3_entries(ram):
    rows = len(ram) // 2048
    out = []
    prev = None
    for row in range(1, rows + 1):
        g = ram[(row - 1) * 2048 + 0x0e]
        if g == 3 and prev != 3:
            out.append(row)
        prev = g
    return out

def run_core(inputs, frames, tmp):
    ip = os.path.join(tmp, "in.bin"); rp = os.path.join(tmp, "out.ram")
    open(ip, "wb").write(inputs)
    subprocess.run([HARNESS, CORE, ROM, ip, "--input-skip", "2", "--frames", str(frames), "--ram", rp, "--quiet"],
                   check=True, stdout=subprocess.DEVNULL)
    return open(rp, "rb").read()

def first_ges3(ram, lo, hi):
    for f in range(lo, hi):
        if ram[f * 2048 + 0x0e] == 3:
            return f
    return None

def main():
    args = sys.argv[1:]
    ramp, inp, earlier = "data/wr/fceux_wr.ram", "data/wr/wr_inputs.bin", 3
    i = 0
    while i < len(args):
        if args[i] == "--ram": ramp = args[i + 1]; i += 2
        elif args[i] == "--inputs": inp = args[i + 1]; i += 2
        elif args[i] == "--earlier": earlier = int(args[i + 1]); i += 2
        else: raise SystemExit("unknown option " + args[i])
    ram = open(ramp, "rb").read()
    wr = open(inp, "rb").read()
    tmp = tempfile.mkdtemp(prefix="pipescan_")
    entries = ges3_entries(ram)
    print(f"{len(entries)} vertical pipe entries in the dump (rows): {entries}")
    gain_total = 0
    for row in entries:
        f_wr = row - 3                      # QuickNES frame of the entry
        rec_wr = row - 2                    # record carrying the WR's Down
        base = run_core(wr, f_wr + 4, tmp)
        f0 = first_ges3(base, f_wr - 8, f_wr + 4)
        best = None
        for k in range(1, earlier + 1):
            m = bytearray(wr); m[rec_wr - k] |= DOWN
            r = run_core(bytes(m), f_wr + 4, tmp)
            fk = first_ges3(r, f_wr - 8, f_wr + 4)
            if fk is not None and fk < f0:
                best = (k, fk)
        x = ram[(row - 1) * 2048 + 0x86] + 256 * ram[(row - 1) * 2048 + 0x6d]
        if best:
            gain_total += f0 - best[1]
            print(f"row {row} (QuickNES frame {f0}, X {x}): Down {best[0]} record(s) earlier enters at frame {best[1]} -> {f0 - best[1]} frame(s) EARLIER")
        else:
            print(f"row {row} (QuickNES frame {f0}, X {x}): optimal (Down up to {earlier} records earlier changes nothing)")
    print(f"total frames available from earlier Down presses: {gain_total}")

if __name__ == "__main__":
    main()
