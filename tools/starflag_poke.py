#!/usr/bin/env python3
"""H50/F254: measure what a second (third, …) StarFlagObject does to a flag level's exit.

`RunStarFlagObj` is dispatched once per frame *per enemy slot* holding `Enemy_ID` = $31, but
the state it drives is global — except the per-slot `EnemyIntervalTimer` that `DelayToAreaEnd`
blocks on, which IS the framerule (F27). So N star-flag objects should divide the timer
countdown by N and collapse the (v+1)+105 area-end wait.

This script measures it on the core. For each level it:
  1. runs the WR inputs unmodified (control) and finds the frame the star flag appears, the
     slot it lives in, and its coordinates;
  2. re-runs with N-1 copies poked into free enemy slots a few frames later;
  3. reports StarFlagTaskControl's task boundaries and the next area-load frame for both.

Only the end-of-level sequence of the chosen level is affected, so everything before the poke
is the real WR; everything after desyncs (the next level loads early against WR inputs cut for
the old timing) and is not measured.

Usage:
  tools/starflag_poke.py                 # all five flag levels, N=2
  tools/starflag_poke.py --level 8-2 --n 3
  tools/starflag_poke.py --n 2 --n 3 --n 6

RAM addresses (smbdis.asm): $0746 StarFlagTaskControl, $0772 OperMode_Task, $07B1
EventMusicBuffer, $0796+k EnemyIntervalTimer, $16+k Enemy_ID, $0F+k Enemy_Flag,
$87+k Enemy_X_Position, $6E+k Enemy_PageLoc, $B6+k Enemy_Y_HighPos, $CF+k Enemy_Y_Position.
"""
import argparse
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORE_CANDIDATES = ["third_party/QuickNES_Core/quicknes_libretro.dylib",
                   "third_party/QuickNES_Core/quicknes_libretro.so"]
ROM = "roms/Super Mario Bros. (W) [!].nes"
INPUTS = "data/wr/wr_inputs.bin"
HARNESS = "build/harness"

SFTC, OPERTASK, EVTMUS = 0x746, 0x772, 0x7b1
EVTMUSQ, SCROLLLOCK = 0xfc, 0x723
END_OF_LEVEL_MUSIC = 0x20
ENEMY_ID, ENEMY_FLAG = 0x16, 0x0f
ENEMY_X, ENEMY_PAGE, ENEMY_YHI, ENEMY_Y = 0x87, 0x6e, 0xb6, 0xcf
ENEMY_ITIMER = 0x796
STAR_FLAG_OBJECT = 0x31

# Flag levels: (first core frame of the level, core frame to run to).
# Core frame = fceux dump row - 4 (F45 alignment, as used by tools/w82_jump_probe.py); the
# starts are each level's own area load, so the star-flag search cannot pick up an earlier one.
LEVELS = {"1-1": (40, 2100), "4-1": (3812, 6200), "8-1": (7769, 10950),
          "8-2": (10811, 13100), "8-3": (12954, 15200)}


def core_path():
    for c in CORE_CANDIDATES:
        if os.path.exists(os.path.join(ROOT, c)):
            return c
    sys.exit("no QuickNES core found; run tools/build_core.sh")


def run(frames, ramfile, pokes=()):
    cmd = [os.path.join(ROOT, HARNESS), core_path(), ROM, INPUTS,
           "--frames", str(frames), "--input-skip", "2", "--ram", ramfile, "--quiet"]
    for a, v, f in pokes:
        cmd += ["--poke", "0x%x=0x%x@%d" % (a, v, f)]
    subprocess.run(cmd, cwd=ROOT, check=True)
    with open(ramfile, "rb") as fh:
        return fh.read()


def byte(ram, frame, addr):
    return ram[frame * 0x800 + addr]


def task_boundaries(ram, lo, hi):
    """[(frame, StarFlagTaskControl)] at each change, plus the next area load frame."""
    out, prev = [], None
    load = None
    for f in range(lo, hi):
        v = byte(ram, f, SFTC)
        if v != prev:
            out.append((f, v))
            prev = v
        # an area load is OperMode_Task returning to 0 while OperMode is still game mode
        if load is None and f > lo and byte(ram, f, OPERTASK) == 0 and byte(ram, f - 1, OPERTASK) == 3:
            load = f
    return out, load


def measure(level, n, verbose, nomusic=False):
    start, frames = LEVELS[level]
    with tempfile.TemporaryDirectory() as td:
        ctrl = run(frames, os.path.join(td, "c.ram"))
        # skip past this level's own area load: RAM still holds the previous level's star
        # flag until InitializeArea clears it, and a poke during the load would be wiped.
        for f in range(start, frames):
            if byte(ctrl, f, OPERTASK) == 3 and byte(ctrl, f, SFTC) == 0:
                start = f
                break
        # find the frame this level's star flag is created, and which slot it took
        appear = slot = None
        for f in range(start, frames):
            for k in range(6):
                if byte(ctrl, f, ENEMY_ID + k) == STAR_FLAG_OBJECT and byte(ctrl, f, ENEMY_FLAG + k):
                    appear, slot = f, k
                    break
            if appear is not None:
                break
        if appear is None:
            sys.exit("%s: no StarFlagObject found in %d frames" % (level, frames))
        pf = appear + 8                      # poke a few frames after it exists, before task 1
        free = [k for k in range(6)
                if k != slot and byte(ctrl, pf, ENEMY_FLAG + k) == 0][: n - 1]
        if len(free) < n - 1:
            sys.exit("%s: only %d free enemy slots, need %d" % (level, len(free), n - 1))
        pokes = []
        if nomusic:
            # PlayerEndLevel queues EndOfLevelMusic ($20) only if ScrollLock is still set when
            # Mario passes Y >= $ae; with it clear, EventMusicBuffer stays 0 and DelayToAreaEnd's
            # second condition never binds either.  Find the frame the music is queued and clear
            # ScrollLock ($0723) the frame before.
            q = next((f for f in range(appear, frames)
                      if byte(ctrl, f, EVTMUSQ) == END_OF_LEVEL_MUSIC), None)
            if q is None:
                sys.exit("%s: never queues end-of-level music" % level)
            pokes.append((SCROLLLOCK, 0, q - 1))
        for k in free:                       # copy the real star flag into each free slot
            for base in (ENEMY_ID, ENEMY_FLAG, ENEMY_X, ENEMY_PAGE, ENEMY_YHI, ENEMY_Y):
                src = STAR_FLAG_OBJECT if base == ENEMY_ID else (
                    1 if base == ENEMY_FLAG else byte(ctrl, pf, base + slot))
                pokes.append((base + k, src, pf))
        poked = run(frames, os.path.join(td, "p.ram"), pokes)

        cb, cload = task_boundaries(ctrl, appear - 2, frames)
        pb, pload = task_boundaries(poked, appear - 2, frames)
        if verbose:
            print("  star flag: slot %d, appears core %d; poked slots %s at core %d (%d pokes)"
                  % (slot, appear, free, pf, len(pokes)))
            print("  control  SFTC:", " ".join("%d@%d" % (v, f) for f, v in cb if v))
            print("  poked    SFTC:", " ".join("%d@%d" % (v, f) for f, v in pb if v))
        return cb, cload, pb, pload, appear


def phase(b, want):
    for f, v in b:
        if v == want:
            return f
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--level", action="append", choices=sorted(LEVELS))
    ap.add_argument("--n", action="append", type=int, help="star-flag objects (default 2)")
    ap.add_argument("-v", "--verbose", action="store_true")
    ap.add_argument("--no-music", action="store_true",
                    help="also clear ScrollLock so PlayerEndLevel never queues the win music")
    a = ap.parse_args()
    levels = a.level or ["1-1", "4-1", "8-1", "8-2", "8-3"]
    ns = a.n or [2]
    print("level  N   countdown        raise      area-end wait     next load        saved")
    total = {}
    for level in levels:
        for n in ns:
            cb, cl, pb, pl, appear = measure(level, n, a.verbose, a.no_music)
            c2, c3, c4, c5 = (phase(cb, i) for i in (2, 3, 4, 5))
            p2, p3, p4, p5 = (phase(pb, i) for i in (2, 3, 4, 5))
            saved = (cl - pl) if (cl and pl) else None
            total[n] = total.get(n, 0) + (saved or 0)
            # when task 4 is skipped entirely (SFTC 3 -> 5 in one frame) phase(4) is None:
            # the raise is 3->5 and the area-end wait is 0.
            if p4 is None and p5 is not None:
                p4 = p5
            d = lambda a, b: ("%4d" % (b - a)) if (a is not None and b is not None) else "   ?"
            print("%-5s  %d   %s -> %-4s   %s -> %-3s  %s -> %-4s     %5s -> %-5s   %4s"
                  % (level, n, d(c2, c3), d(p2, p3).strip(), d(c3, c4).strip(), d(p3, p4).strip(),
                     d(c4, c5), d(p4, p5).strip(), cl, pl,
                     saved if saved is not None else "?"))
    for n, s in sorted(total.items()):
        print("TOTAL over %d level(s), N=%d: %d frames" % (len(levels), n, s))


if __name__ == "__main__":
    main()
