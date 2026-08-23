#!/usr/bin/env python3
"""Compare the model's block-state bookkeeping (smb-opt `tracec CASE ... ` "blocks:" lines, Options::BlockStates)
with the WR dump frame by frame: the $23 cell in the block buffer, the $c4 cells, BrickCoinTimer/Flag,
IntervalTimerControl, FrameCounter & 7, AreaParserTaskNum, CurrentPageLoc*16 + CurrentColumnPos, VRAM_Buffer1
non-empty, VRAM_Buffer_AddrCtrl == 6. Alignment: step i of `tracec CASE INPUTS FIRST N` acts on record FIRST+i,
which the dump applies in row FIRST+i+2 (F69); the trace's post-step line is compared with that row.

Usage: tools/block_state_check.py TRACE_FILE RAMFILE FIRST_RECORD [--verbose]
"""
import re, sys
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from ram_trace import load_symbols

IP0, FC0, GT0 = 4, 41, 24   # W42Main (dump row 6585); make these per-case if other cases get block states

def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    verbose = '--verbose' in sys.argv
    trace, ramfile, first = args[0], args[1], int(args[2])
    syms = load_symbols()
    data = open(ramfile, 'rb').read()
    def byte(row, addr): return data[(row - 1) * 2048 + addr]
    rows = {}
    step = None
    for line in open(trace):
        m = re.match(r'^(\d+) 0x', line)
        if m: step = int(m.group(1)); continue
        m = re.match(r'^blocks: bounce (\d+) used (0x[0-9a-f]+) cbt (\w+)/(\d+) f (\d+) aptn (\d+) bp (\w+) col (\d+) vb1 (\w+) a6 (\w+)', line)
        if m and step is not None:
            f = int(m.group(5))
            rows[step] = dict(bounce=int(m.group(1)), used=int(m.group(2), 16), flag=m.group(3) == 'true', cbt=int(m.group(4)),
                              ip=(IP0 - f) % 21, fc=(FC0 + f) & 7, gt=(GT0 - f) % 24 or 24, aptn=int(m.group(6)), col=int(m.group(8)),
                              vb1=m.group(9) == 'true', a6=m.group(10) == 'true')
    n, mism = 0, []
    for step in sorted(rows):
        row = first + step + 2
        mr = rows[step]
        # block buffer: which cell holds $23 (absolute column needs the page: even pages at $0500, odd at $05d0)
        cells23 = []
        for half, base in ((0, 0x500), (1, 0x5d0)):
            for y in range(13):
                for x in range(16):
                    if byte(row, base + y * 16 + x) == 0x23: cells23.append((half, x, y))
        model23 = None
        if mr['bounce']:
            v = mr['bounce'] - 1; cx, cy = v >> 4, v & 15
            model23 = ((cx >> 4) & 1, cx & 15, cy)
        core = dict(
            bounce=cells23[0] if cells23 else None,
            flag=byte(row, syms['BrickCoinTimerFlag']) != 0, cbt=byte(row, syms['BrickCoinTimer']),
            ip=byte(row, syms['IntervalTimerControl']), fc=byte(row, syms['FrameCounter']) & 7,
            gt=byte(row, syms['GameTimerCtrlTimer']), aptn=byte(row, syms['AreaParserTaskNum']), col=byte(row, syms['CurrentPageLoc']) * 16 + byte(row, syms['CurrentColumnPos']),
            vb1=byte(row, syms['VRAM_Buffer1']) != 0, a6=byte(row, syms['VRAM_Buffer_AddrCtrl']) == 6)
        model = dict(mr); model['bounce'] = model23
        n += 1
        for k in core:
            if model[k] != core[k]:
                mism.append((row, k, model[k], core[k]))
                if verbose: print(f"row {row} step {step} {k}: model {model[k]} core {core[k]}")
        if len(cells23) > 1: print(f"row {row}: {len(cells23)} cells hold $23: {cells23}")
    print(f"compared {n} rows; {len(mism)} field mismatches")
    if mism and not verbose:
        for m in mism[:10]: print("  row %d %s: model %s core %s" % m)

if __name__ == '__main__':
    main()
