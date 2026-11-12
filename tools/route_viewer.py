#!/usr/bin/env python3
"""Route viewer data builder: replays a movie on the QuickNES core with pictures (build/viewdump),
stitches one background panorama per area (most common colour per pixel, so sprites vanish),
and writes the per-frame route + per-level framerule stats for viewer/index.html.

usage: tools/route_viewer.py [MOVIE.fm2] [OUTDIR]
  defaults: data/wr/maru-rtarules.fm2 -> viewer/
  build first: cc -O2 -o build/viewdump src/fastcore/viewdump.c -I third_party/QuickNES_Core/libretro/libretro-common/include
Writes OUTDIR/pano/<seg>.png and OUTDIR/route.js (window.ROUTE = {...}). Scratch files go to runs/viewer/.
Picture of frame f is drawn with the camera of frame f-1 (measured: tools/route_viewer.py header, F322).
"""
import json, os, re, struct, subprocess, sys, zlib

CORE = "third_party/QuickNES_Core/quicknes_libretro.dylib"
if not os.path.exists(CORE): CORE = "third_party/QuickNES_Core/quicknes_libretro.so"
ROM = "roms/smb.nes" if os.path.exists("roms/smb.nes") else "roms/Super Mario Bros. (W) [!].nes"
TMP = "runs/viewer"
# HappyLee #1715M per-level frames (load -> next load), F29
WR_FRAMES = {"1-1": 1902, "1-2": 1870, "4-1": 2228, "4-2": 1729, "8-1": 3042, "8-2": 2143, "8-3": 2101, "8-4": 2810}

def png(path, w, h, rgb):
    raw = b"".join(b"\0" + rgb[y * w * 3:(y + 1) * w * 3] for y in range(h))
    def chunk(t, d): return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff)
    open(path, "wb").write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
                           + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))

def main():
    movie = sys.argv[1] if len(sys.argv) > 1 else "data/wr/maru-rtarules.fm2"
    out = sys.argv[2] if len(sys.argv) > 2 else "viewer"
    os.makedirs(TMP, exist_ok=True); os.makedirs(f"{out}/pano", exist_ok=True)
    pre = f"{TMP}/movie"
    subprocess.run(["python3", "tools/fm2_to_inputs.py", movie, f"{pre}_inputs.bin"], check=True)
    subprocess.run(["./build/viewdump", "dump", CORE, ROM, f"{pre}_inputs.bin", pre, "--input-skip", "2", "--reset0"], check=True)
    inp = open(f"{pre}_inputs.bin", "rb").read()[2:]
    d = open(f"{pre}.ram", "rb").read(); n = len(d) // 2048
    b = lambda i, a: d[i * 2048 + a]
    cam = lambda i: b(i, 0x71a) * 256 + b(i, 0x71c)
    px = lambda i: b(i, 0x6d) * 256 + b(i, 0x86)
    task = lambda i: b(i, 0x772)
    # end of run = axe (OperMode 2) or end of dump
    end = next((i for i in range(n) if b(i, 0x770) == 2), n - 1)
    # area loads: OperMode 1, task -> 0 ; split on loop pull-backs (x jumps back > 256 in play)
    loads = [i for i in range(1, end) if b(i, 0x770) == 1 and task(i) == 0 and task(i - 1) != 0]
    cuts = sorted(set(loads + [i for i in range(1, end) if task(i) == 3 and task(i - 1) == 3
                                and px(i - 1) - px(i) > 256]))
    segs = []
    for k, a in enumerate(cuts):
        z = (cuts[k + 1] - 1) if k + 1 < len(cuts) else end
        play = [i for i in range(a, z + 1) if b(i, 0x770) == 1 and task(i) == 3]
        if not play: continue
        segs.append({"first": a, "last": z, "play0": play[0], "w": b(play[0], 0x75f) + 1, "l": b(play[0], 0x75c) + 1,
                     "loop": a not in loads})
    # name segments: per level, room index
    per = {}
    for s in segs:
        lv = f"{s['w']}-{s['l']}"; per[lv] = per.get(lv, 0) + 1
        s["level"] = lv; s["idx"] = per[lv]; s["name"] = f"{lv.replace('-', '_')}_{per[lv]}"
    # world/level of a segment = level being played when it STARTS (warp pipes change W during the descent)
    camf = [-1] * n
    for s in segs:
        for f in range(s["first"] + 1, s["last"] + 1):
            if task(f) == 3 and task(f - 1) == 3 and b(f, 0x770) == 1: camf[f] = cam(f - 1)
    open(f"{pre}.cam", "wb").write(struct.pack(f"<{n}i", *camf))
    with open(f"{TMP}/segs.txt", "w") as fh:
        for s in segs: fh.write(f"{s['name']} {s['first']} {s['last']}\n")
    r = subprocess.run(["./build/viewdump", "stitch", pre, f"{TMP}/segs.txt", TMP], check=True, capture_output=True, text=True)
    for line in r.stdout.splitlines():
        name, w, h, lo = line.split()[:4]; w, h, lo = int(w), int(h), int(lo)
        s = next(s for s in segs if s["name"] == name)
        s.update(pw=w, ph=h, x0=lo)
        png(f"{out}/pano/{name}.png", w, h, open(f"{TMP}/{name}.rgb", "rb").read())
        os.remove(f"{TMP}/{name}.rgb")
        print("pano", name, w, h, flush=True)
    # per-frame route
    for s in segs:
        fr = []
        for f in range(s["first"], s["last"] + 1):
            if not (b(f, 0x770) == 1 and task(f) == 3): continue
            spd = b(f, 0x57); spd = spd - 256 if spd > 127 else spd
            yh = b(f, 0xb5)
            fr.append([f, px(f) + b(f, 0x400) / 256, (yh - 1) * 256 + b(f, 0xce) + b(f, 0x416) / 256, spd, b(f, 0x705),
                       b(f, 0x0e), b(f, 0x1d), b(f, 0x704), b(f, 0x754), inp[f] if f < len(inp) else 0, cam(f), b(f, 0x77f),
                       int(f"{b(f, 0x7f8)}{b(f, 0x7f9)}{b(f, 0x7fa)}")])
        s["frames"] = fr
    # framerule stats from tools/slack_table.py (row = frame + 1)
    st = subprocess.run(["python3", "tools/slack_table.py", f"{pre}.ram"], check=True, capture_output=True, text=True).stdout
    levels = []
    for line in st.splitlines():
        c = [x.strip() for x in line.strip().strip("|").split("|")]
        if len(c) > 15 and re.fullmatch(r"\d-\d", c[0]):
            lv = c[0]
            levels.append({"level": lv, "load": int(c[1]) - 1, "control": int(c[3]) - 1, "end_event": c[4],
                           "event": int(c[5]) - 1, "next_load": int(c[6]) - 1, "frames": int(c[7]),
                           "slack": c[12], "deficit": c[13], "timer": c[17], "wr_frames": WR_FRAMES.get(lv)})
    data = {"movie": movie, "core": "QuickNES (input-skip 2, reset0)", "total_frames": end + 1,
            "fields": ["frame", "x", "y", "speed", "subspeed", "ges", "state", "swim", "small", "input", "cam", "itc", "timer"],
            "segments": [{k: v for k, v in s.items()} for s in segs], "levels": levels}
    open(f"{out}/route.js", "w").write("window.ROUTE=" + json.dumps(data, separators=(",", ":")) + ";\n")
    print("segments", len(segs), "levels", len(levels), "->", f"{out}/route.js")

if __name__ == "__main__":
    main()
