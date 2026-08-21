#!/usr/bin/env python3
"""Slack table for a full-RAM per-frame dump of an SMB1 movie (tools/lua/wr_dump_fceux.lua).

Row i (1-based) of the dump = fm2 frame i-1 (F25). Mechanism (data/disasm/smbdis.asm):
- A flagpole level ends when StarFlagTaskControl ($0746) reaches 5. Task 3 (RaiseFlagSetoffFWorks)
  raises the star flag 1 px/frame to Y<$72 (firing fireworks if any), then sets the star-flag
  object's EnemyIntervalTimer ($0796+slot) = 6 and moves to task 4 in the same frame (T_set).
  Task 4 (DelayToAreaEnd) waits until that timer is 0 AND EventMusicBuffer ($07B1) is 0.
- Interval timers decrement only on frames where IntervalTimerControl ($077F) wraps (every 21
  frames); DecTimers runs before the game logic in the NMI. With post-frame ITC = v at T_set the
  timer expires at T_set + (v+1) + 5*21.  => slack = v frames (T_set could be later at no cost);
  deficit = 21 - v frames (T_set must be earlier to save a whole framerule).
- Pipe levels (1-2, 4-2) end via VerticalPipeEntry + ChangeAreaTimer ($06DE), a per-frame countdown
  (no ITC quantization at the pipe itself) — but every area load runs ScreenRoutines whose
  intermission card waits on ScreenTimer ($07A0) = 7, another interval timer, so control starts at
  load + 147 + u with u = post-frame ITC at the load row (verified per load below). Hence for a
  pipe level: slack = u, deficit = 21 - u, measured at the NEXT level's load row. Flag-level loads
  always land on u = 19 (expiry + 1), so for them only the end quantization matters.
- 8-4 ends on the axe (OperMode -> 2): no quantization; the bar is the axe frame itself.
Levels are segmented by area-load rows (OperMode_Task -> 0) grouped by (World, Level).
Usage: tools/slack_table.py data/wr/fceux_wr.ram [movie.fm2]   (prints markdown)
"""
import csv, sys

RAM = 0x800
OperMode, Task, GES, World, Level, AreaNum = 0x0770, 0x0772, 0x0E, 0x075F, 0x075C, 0x0760
ITC, SFTC, EMB, CAT, RNG, ALT = 0x077F, 0x0746, 0x07B1, 0x06DE, 0x07A7, 0x0752
T0, T1, T2 = 0x07F8, 0x07F9, 0x07FA
STAR_FLAG_ID = 0x31

def main():
    path = sys.argv[1]
    data = open(path, "rb").read()
    n = len(data) // RAM
    def b(i, a):
        return data[(i - 1) * RAM + a]
    def timer(i):
        return f"{b(i, T0)}{b(i, T1)}{b(i, T2)}"
    lag_rows = set()
    try:
        for r in csv.DictReader(open(path[:-4] + ".csv")):
            if r["lag"] == "1":
                lag_rows.add(int(r["i"]))
    except FileNotFoundError:
        pass
    axe = next((i for i in range(1, n + 1) if b(i, OperMode) == 2), None)
    loads = [i for i in range(2, n + 1) if b(i, OperMode) == 1 and b(i, Task) == 0 and (b(i - 1, Task) != 0 or b(i - 1, OperMode) != 1)]
    levels = []   # [name, start, [sub-loads]]
    for i in loads:
        name = f"{b(i, World)+1}-{b(i, Level)+1}"
        if levels and levels[-1][0] == name:
            levels[-1][2].append(i)
        else:
            levels.append([name, i, [i]])
    print(f"dump: {n} rows; axe row {axe}; area loads: {loads}")
    print()
    hdr = ["Level", "load row", "sub-area loads (AreaNum/AltEntr)", "control row", "end event", "event row", "next load", "frames", "lag",
           "ITC@load", "T_set", "v", "slack", "deficit", "timer expiry (pred/obs)", "music end", "SFTC=5", "timer@event", "RNG@load $07A7-AD"]
    print("| " + " | ".join(hdr) + " |"); print("|" + "---|" * len(hdr))
    for li, (name, start, subs) in enumerate(levels):
        end = levels[li + 1][1] if li + 1 < len(levels) else axe
        ctrl = next((i for i in range(start, end) if b(i, GES) == 8 and b(i, Task) == 3), None)
        after = ctrl or start
        grab = next((i for i in range(after, end) if b(i, GES) in (4, 5)), None)
        pipes = [i for i in range(after + 1, end) if b(i, GES) in (2, 3) and b(i - 1, GES) not in (2, 3)]
        lag = sum(1 for i in lag_rows if start <= i < end)
        rng = " ".join(f"{b(start, RNG + k):02x}" for k in range(7))
        subtxt = ", ".join(f"{i} ({b(i, AreaNum)}/{b(i, ALT)})" for i in subs)
        tset = v = slack = deficit = texp = mend = s5 = "-"
        if li + 1 == len(levels) and axe:
            evt, evrow = "axe (OperMode=2)", axe
        elif grab:
            evt = "flag slide (GES=4)" if b(grab, GES) == 4 else "flag glitch (GES=5)"
            evrow = grab
            tset = next((i for i in range(after, end + 1) if b(i, SFTC) == 4 and b(i - 1, SFTC) == 3), None)
            s5 = next((i for i in range(after, end + 1) if b(i, SFTC) == 5), None)
            slot = next((x for x in range(6) if b(tset, 0x16 + x) == STAR_FLAG_ID), None)
            tobs = next((i for i in range(tset, end + 1) if b(i, 0x0796 + slot) == 0), None) if slot is not None else None
            v = b(tset, ITC); slack, deficit = v, 21 - v
            texp = f"{tset + v + 1 + 105}/{tobs}"
            mend = next((i for i in range(tset, end + 1) if b(i, EMB) == 0), None)
        else:
            p = pipes[-1]
            evt, evrow = f"pipe entry (GES={b(p, GES)}, CAT={b(p, CAT)})", p
            u = b(end, ITC); v = f"u={u}"; slack, deficit = u, 21 - u; tset = f"next load {end}"
        print(f"| {name} | {start} | {subtxt} | {ctrl} | {evt} | {evrow} | {end} | {end - start} | {lag} | {b(start, ITC)} | {tset} | {v} | {slack} | {deficit} | {texp} | {mend} | {s5} | {timer(evrow)} | {rng} |")
    print()
    print("Area loads (ScreenRoutines start wait). control = first GES==8 with Task==3 after the load; check: control - load - 147 - u")
    print("| load row | W-L | AreaNum/AltEntr | u=ITC@load | task 0→1→2→3 rows | ScreenTimer=7 set rows (ITC) | ScreenTimer→0 rows | control row | control-load | check |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    for L in loads:
        nxt = next((x for x in loads if x > L), axe or n)
        tasks = []
        for t in (1, 2, 3):
            r = next((i for i in range(L, nxt) if b(i, Task) == t), None); tasks.append(r)
        sets = [(i, b(i, ITC)) for i in range(L, nxt) if b(i, 0x07A0) == 7 and b(i - 1, 0x07A0) != 7]
        zeros = [i for i in range(L + 1, nxt) if b(i, 0x07A0) == 0 and b(i - 1, 0x07A0) != 0]
        ctrl = next((i for i in range(L, nxt) if b(i, GES) == 8 and b(i, Task) == 3), None)
        u = b(L, ITC)
        chk = (ctrl - L - 147 - u) if ctrl else None
        print(f"| {L} | {b(L, World)+1}-{b(L, Level)+1} | {b(L, AreaNum)}/{b(L, ALT)} | {u} | {tasks} | {sets} | {zeros} | {ctrl} | {ctrl - L if ctrl else None} | {chk} |")
    total = sum(1 for i in lag_rows if i <= (axe or n))
    print(f"\nTotals: rows 1..{axe} = {axe} frames to the axe (fm2 frame {axe-1}); lag frames to the axe: {total}")
    if len(sys.argv) > 2:
        inp = [l for l in open(sys.argv[2], encoding="utf-8", errors="replace") if l.startswith("|")]
        last = max(j for j, l in enumerate(inp) if l.split("|")[2] != "........")
        print(f"Ending coast: last input on fm2 frame {last} (0-based); axe on fm2 frame {axe-1}: {axe-1-last} input-free frames")

if __name__ == "__main__":
    main()
