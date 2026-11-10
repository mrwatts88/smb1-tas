#!/usr/bin/env python3
"""Exact SMB1 vertical jump physics (ImposeGravity) for the 8-4 ending arithmetic.

Validated against the WR dump: hold 6 from Y=128 gives 123,118,113,108,104,100,96,92,89,87,85,84,83,83,
84,85,86,88,91,94,98,102,106,110.
"""
import sys

CLASSES = {  # x-speed class -> (init speed, rise force, fall force)
    0: (-4, 0x20, 0x70),
    1: (-4, 0x20, 0x70),
    2: (-4, 0x1E, 0x60),
    3: (-5, 0x28, 0x90),
    4: (-5, 0x28, 0x90),
}


def jump(y0, hold, cls=4, frames=80, start_dummy=0):
    """Return list of (Y, speed) after each airborne frame n=1.. for a jump with A held `hold` frames."""
    spd, rise, fall = CLASSES[cls]
    force = rise
    y = y0
    dummy = start_dummy
    mf = 0
    out = []
    for n in range(1, frames + 1):
        a_now = n <= hold
        a_prev = (n - 1) <= hold and n > 1
        # JumpSwimSub: if rising and not (A now and A prev) and risen >= 1 px -> fall force
        if spd >= 0:
            force = fall
        elif not (a_now and a_prev):
            if (y0 - y) >= 1:
                force = fall
        # ImposeGravity
        dummy += mf
        c = dummy >> 8
        dummy &= 0xFF
        y = y + spd + c
        mf += force
        c2 = mf >> 8
        mf &= 0xFF
        spd += c2
        if spd >= 4 and mf >= 0x80:
            spd = 4
            mf = 0
        out.append((y, spd))
    return out


def main():
    y0 = 128
    lo, hi = 96, 112  # Mario Y window with feet (Y+32) inside row 6 (the axe row)
    for cls in (4, 2, 0):
        print(f"class {cls}: hold -> frames n with Y in [{lo},{hi}) and speed>=0 ; coast C = n_max - hold")
        best = None
        for hold in range(1, 41):
            tr = jump(y0, hold, cls)
            ns = [n for n, (y, s) in enumerate(tr, 1) if lo <= y < hi and s >= 0]
            apex = min(y for y, _ in tr)
            if ns:
                c = max(ns) - hold
                print(f"  hold {hold:2d}: apex Y {apex:3d}  n in {ns[0]}..{ns[-1]}  C={c}")
                if best is None or c > best[0]:
                    best = (c, hold)
            else:
                print(f"  hold {hold:2d}: apex Y {apex:3d}  never in window")
        print("  best C,hold:", best)
    # validation print
    print("validate hold 6:", [y for y, _ in jump(128, 6)][:25])
    print("validate hold 32:", [y for y, _ in jump(128, 32)][:58])


if __name__ == "__main__":
    main()
