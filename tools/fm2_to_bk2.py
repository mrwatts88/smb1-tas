#!/usr/bin/env python3
"""Convert an FCEUX .fm2 (NES, version 3) to a BizHawk .bk2 for the NesHawk core, offline.

Mirrors BizHawk 2.11.1's Fm2Import (src/BizHawk.Client.Common/movie/import/Fm2Import.cs) but
without its "ROM required to populate hash" dialog, which blocks headless runs.
  fm2 line: |cmd|RLDUTSBA|RLDUTSBA||   cmd bit 1 = soft reset, bit 2 = power
  bk2 line: |rP|UDLRsSBA|UDLRsSBA|     LogKey: #Reset|Power|#P1 Up|...|P1 A|#P2 Up|...
Usage: tools/fm2_to_bk2.py movie.fm2 out.bk2 [--rom rom.nes] [--core NesHawk]
"""
import argparse, hashlib, zipfile

FM2_ORDER = "RLDUTSBA"                      # Right Left Down Up sTart Select B A
BK2_NAMES = ["Up", "Down", "Left", "Right", "Select", "Start", "B", "A"]
BK2_MNEMONIC = "UDLRsSBA"

def convert_pad(f):
    pressed = {FM2_ORDER[i]: (f[i] != ".") for i in range(8)}
    bits = [pressed["U"], pressed["D"], pressed["L"], pressed["R"], pressed["S"], pressed["T"], pressed["B"], pressed["A"]]
    return "".join(m if b else "." for m, b in zip(BK2_MNEMONIC, bits))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("fm2"); ap.add_argument("out"); ap.add_argument("--rom"); ap.add_argument("--core", default="NesHawk")
    ap.add_argument("--emu-version", default="2.11.1")
    a = ap.parse_args()
    header, inputs, comments = {}, [], []
    for line in open(a.fm2, encoding="utf-8", errors="replace"):
        line = line.rstrip("\r\n")
        if not line:
            continue
        if line.startswith("|"):
            inputs.append(line)
        else:
            k, _, v = line.partition(" ")
            if k == "comment":                      # "comment author  HappyLee" -> key "comment author"
                k2, _, v2 = v.partition(" ")
                k, v = f"comment {k2}", v2
                comments.append(line)
            elif k == "subtitle":
                comments.append(line)
            header[k] = v
    port0 = header.get("port0", "1") == "1"
    port1 = header.get("port1", "1") == "1"
    logkey = "#Reset|Power|"
    for p, on in ((1, port0), (2, port1)):
        if on:
            logkey += "#" + "".join(f"P{p} {n}|" for n in BK2_NAMES)
    lines = ["[Input]", "LogKey:" + logkey]
    for l in inputs:
        f = l.split("|")          # ['', cmd, p1, p2, ..., '']
        cmd = int(f[1]) if f[1].strip() else 0
        s = "|" + ("r" if cmd & 1 else ".") + ("P" if cmd & 2 else ".") + "|"
        if port0: s += convert_pad(f[2]) + "|"
        if port1: s += convert_pad(f[3] if len(f) > 3 and len(f[3]) >= 8 else "........") + "|"
        lines.append(s)
    lines.append("[/Input]")
    input_log = "\r\n".join(lines) + "\r\n"

    hdr = [("MovieVersion", "BizHawk v2.0.0"),
           ("Author", header.get("comment author", "").strip()),
           ("emuVersion", f"Version {a.emu_version}"),
           ("OriginalEmuVersion", f"Version {a.emu_version}"),
           ("Platform", "NES"),
           ("GameName", header.get("romFilename", "")),
           ("Core", a.core),
           ("rerecordCount", header.get("rerecordCount", "0"))]
    if a.rom:
        data = open(a.rom, "rb").read()
        body = data[16:] if data[:4] == b"NES\x1a" else data
        hdr.append(("SHA1", hashlib.sha1(body).hexdigest().upper()))
        hdr.append(("MD5", hashlib.md5(body).hexdigest().upper()))
    if header.get("palFlag", "0") == "1":
        hdr.append(("PAL", "1"))
    header_txt = "".join(f"{k} {v}\r\n" for k, v in hdr)
    sync = ('{"o":{"$type":"BizHawk.Emulation.Cores.Nintendo.NES.NES+NESSyncSettings, BizHawk.Emulation.Cores",'
            '"BoardProperties":{},"RegionOverride":"Default",'
            '"Controls":{"NesLeftPort":"%s","NesRightPort":"%s","Famicom":false,"FamicomExpPort":"UnpluggedFam"},'
            '"InitialWRamStatePattern":[]}}') % ("ControllerNES" if port0 else "UnpluggedNES", "ControllerNES" if port1 else "UnpluggedNES")
    with zipfile.ZipFile(a.out, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("Header.txt", header_txt)
        z.writestr("Comments.txt", "".join(c + "\r\n" for c in comments))
        z.writestr("Subtitles.txt", "")
        z.writestr("SyncSettings.json", sync)
        z.writestr("Input Log.txt", input_log)
    print(f"wrote {a.out}: {len(inputs)} frames, LogKey {logkey}")

if __name__ == "__main__":
    main()
