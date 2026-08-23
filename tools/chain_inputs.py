#!/usr/bin/env python3
"""Concatenate NES-order input files (one byte per record, as written by `smb-opt bfscx-path --out`) into one
file, optionally prefixed by a slice of another input file (e.g. WR records). P2.3c-2c: builds the chained
top-route reference path segment by segment.

usage: tools/chain_inputs.py OUT [--prefix FILE:FIRST:N] SEG1 [SEG2 ...]
Prints the record count of every part and the total (= the PREFIX argument for the next `bfscx` segment)."""
import sys

def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__); sys.exit(2)
    out = args[0]; parts = []; i = 1
    while i < len(args):
        if args[i] == '--prefix':
            f, first, n = args[i + 1].split(':'); i += 2
            data = open(f, 'rb').read()[int(first):int(first) + int(n)]
            parts.append((f'{f}[{first}:{int(first) + int(n)}]', data))
        else:
            parts.append((args[i], open(args[i], 'rb').read())); i += 1
    total = b''.join(d for _, d in parts)
    open(out, 'wb').write(total)
    for name, d in parts: print(f'{len(d):5d}  {name}')
    print(f'{len(total):5d}  total -> {out}')

if __name__ == '__main__':
    main()
