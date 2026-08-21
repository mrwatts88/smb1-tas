#!/usr/bin/env python3
"""Verify a SMB1 ROM against TASVideos #1715M expectations.

Usage: tools/verify_rom.py <rom.nes> [--fm2 data/wr/happylee-supermariobros,warped.fm2]
                                     [--write-classic roms/"Super Mario Bros. (W) [!].nes"]
Checks: iNES header sanity (32K PRG, 8K CHR, mapper 0), headerless MD5 vs the movie's
romChecksum (FCEUX hashes PRG+CHR only), and the classic-iNES-headered MD5/SHA1 vs TASVideos'
listing for "Super Mario Bros. (W) [!].nes" (https://tasvideos.org/Games/1).
Exit code 0 = all checks passed.
"""
import argparse, base64, hashlib, pathlib, sys

TASVIDEOS_W_MD5 = "811b027eaf99c2def7b933c5208636de"
TASVIDEOS_W_SHA1 = "ea343f4e445a9050d4b4fbac2c77d0693b1d0922"
# 32K PRG, 8K CHR, mapper 0, vertical mirroring — the header on TASVideos' file
CLASSIC_HEADER = bytes.fromhex("4e45531a020101000000000000000000")


def fm2_checksum(path):
    for line in open(path, "r", encoding="utf-8", errors="replace"):
        if line.startswith("romChecksum"):
            return line.split("base64:")[1].strip()
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("rom")
    ap.add_argument("--fm2", default=None)
    ap.add_argument("--write-classic", default=None,
                    help="write a copy with the classic iNES header (byte-identical to TASVideos' file)")
    a = ap.parse_args()
    data = pathlib.Path(a.rom).read_bytes()
    ok = True
    if data[:4] != b"NES\x1a":
        print("FAIL: not an iNES file")
        sys.exit(1)
    hdr, body = data[:16], data[16:]
    prg, chr_ = hdr[4] * 16384, hdr[5] * 8192
    mapper = (hdr[6] >> 4) | (hdr[7] & 0xF0)
    nes2 = (hdr[7] & 0x0C) == 0x08
    print(f"header: {hdr.hex()}  ({'NES 2.0' if nes2 else 'iNES'})")
    print(f"PRG {prg}  CHR {chr_}  mapper {mapper}  mirroring {'vertical' if hdr[6] & 1 else 'horizontal'}  data {len(body)} bytes")
    if (prg, chr_, mapper, len(body)) != (32768, 8192, 0, 40960):
        print("FAIL: expected 32K PRG + 8K CHR, mapper 0, 40960 data bytes")
        ok = False
    body_md5 = hashlib.md5(body).hexdigest()
    body_b64 = base64.b64encode(bytes.fromhex(body_md5)).decode()
    print(f"headerless md5  {body_md5}  (fm2 form: base64:{body_b64})")
    print(f"headerless sha1 {hashlib.sha1(body).hexdigest()}")
    classic = CLASSIC_HEADER + body
    cmd5, csha1 = hashlib.md5(classic).hexdigest(), hashlib.sha1(classic).hexdigest()
    print(f"classic-headered md5 {cmd5}  sha1 {csha1}")
    if (cmd5, csha1) == (TASVIDEOS_W_MD5, TASVIDEOS_W_SHA1):
        print("OK: data matches TASVideos 'Super Mario Bros. (W) [!].nes'")
    else:
        print("FAIL: data does not match TASVideos 'Super Mario Bros. (W) [!].nes'")
        ok = False
    if a.fm2:
        want = fm2_checksum(a.fm2)
        print(f"movie romChecksum: base64:{want}")
        if want == body_b64:
            print("OK: matches the movie's romChecksum")
        else:
            print("FAIL: movie romChecksum differs")
            ok = False
    if a.write_classic:
        pathlib.Path(a.write_classic).write_bytes(classic)
        print(f"wrote {a.write_classic} ({len(classic)} bytes)")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
