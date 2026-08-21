#!/usr/bin/env python3
"""Summarize an FCEUX .fm2 movie: header, frame count, first Start press, last input frame,
Left+Right / Up+Down frames, reset commands, per-button counts.

Usage: tools/fm2_info.py <movie.fm2> [--list-lr]
fm2 input line format: |commands|RLDUTSBA|RLDUTSBA||  (P1 then P2; '.' = not pressed)
"""
import argparse

BTN = "RLDUTSBA"  # Right Left Down Up sTart Select B A
FPS = 60.0988


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("fm2")
    ap.add_argument("--list-lr", action="store_true", help="list the frames with L+R / U+D")
    a = ap.parse_args()
    header, inputs = [], []
    for line in open(a.fm2, "r", encoding="utf-8", errors="replace"):
        line = line.rstrip("\r\n")
        (inputs if line.startswith("|") else header).append(line)

    def p1(l):
        f = l.split("|")
        return f[2] if len(f) > 2 else "........"

    def cmd(l):
        f = l.split("|")
        return int(f[1]) if len(f) > 1 and f[1].isdigit() else 0

    print("== header ==")
    for h in header:
        print(" ", h)
    n = len(inputs)
    print(f"== frames == {n}  (= {n / FPS:.3f} s at {FPS} fps)")
    pressed = [i for i, l in enumerate(inputs) if any(c != "." for c in p1(l))]
    last = pressed[-1] if pressed else None
    if last is not None:
        print(f"last frame with P1 input: {last} (0-based) = {last + 1} (1-based); "
              f"trailing input-free frames: {n - 1 - last}; buttons on that frame: {p1(inputs[last])}")
    first_start = next((i for i, l in enumerate(inputs) if p1(l)[4] != "."), None)
    print(f"first Start press: frame {first_start} (0-based)")
    resets = [i for i, l in enumerate(inputs) if cmd(l)]
    print(f"frames with commands (1=soft reset, 2=power): {[(i, cmd(inputs[i])) for i in resets[:10]]}"
          f"{' ...' if len(resets) > 10 else ''}")
    lr = [i for i, l in enumerate(inputs) if p1(l)[0] != "." and p1(l)[1] != "."]
    ud = [i for i, l in enumerate(inputs) if p1(l)[2] != "." and p1(l)[3] != "."]
    print(f"Left+Right frames: {len(lr)};  Up+Down frames: {len(ud)}")
    if a.list_lr:
        print("  L+R at (0-based):", lr)
        print("  U+D at (0-based):", ud)
    counts = {b: sum(1 for l in inputs if p1(l)[k] != ".") for k, b in enumerate(BTN)}
    print("frames each button is held:", counts)


if __name__ == "__main__":
    main()
