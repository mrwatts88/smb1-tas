#!/usr/bin/env python3
"""Locate the warp / area-loading tables in the SMB1 ROM and print their out-of-bounds reads.

Usage: tools/warp_tables.py [roms/'Super Mario Bros. (W) [!].nes']

Tables are found by byte pattern (taken from data/disasm/smbdis.asm), so the script is independent
of any assembler listing. CPU address = PRG offset + $8000 (32 KiB NROM, 16-byte iNES header).
Everything printed is plain ROM arithmetic; see docs/warp-model.md for the code paths that perform
each lookup.
"""
import sys

ROM = sys.argv[1] if len(sys.argv) > 1 else "roms/Super Mario Bros. (W) [!].nes"
data = open(ROM, "rb").read()
assert data[:4] == b"NES\x1a", "not an iNES file"
prg = data[16:16 + 32 * 1024]
assert len(prg) == 32 * 1024

def find(pattern, name):
    hits = [i for i in range(len(prg) - len(pattern) + 1) if prg[i:i + len(pattern)] == pattern]
    assert len(hits) == 1, f"{name}: expected exactly one hit, got {hits}"
    return hits[0]

def cpu(off):
    return off + 0x8000

def rd(off):
    return prg[off & 0x7FFF]  # 6502 absolute-indexed reads never leave the PRG space here

# --- table locations (patterns = the .db lines in smbdis.asm) -------------------------------
warp_zone_numbers = find(bytes([4, 3, 2, 0, 0x24, 5, 0x24, 0, 8, 7, 6, 0]), "WarpZoneNumbers")
game_text_offsets = warp_zone_numbers + 12
world_addr_offsets = find(bytes([0, 5, 0x0A, 0x0E, 0x13, 0x17, 0x1B, 0x20, 0x25, 0x29, 0xC0, 0x26, 0x60]),
                          "WorldAddrOffsets")
area_addr_offsets = world_addr_offsets + 8          # 36 bytes
enemy_addr_hoffsets = area_addr_offsets + 36        # 4 bytes: 1F 06 1C 00
assert prg[enemy_addr_hoffsets:enemy_addr_hoffsets + 4] == bytes([0x1F, 6, 0x1C, 0])
enemy_data_addr_low = enemy_addr_hoffsets + 4       # 34 bytes
enemy_data_addr_high = enemy_data_addr_low + 34
area_data_hoffsets = enemy_data_addr_high + 34      # 4 bytes: 00 03 19 1C
assert prg[area_data_hoffsets:area_data_hoffsets + 4] == bytes([0, 3, 0x19, 0x1C])
area_data_addr_low = area_data_hoffsets + 4
area_data_addr_high = area_data_addr_low + 34
halfway_nybbles = find(bytes([0x56, 0x40, 0x65, 0x70, 0x66, 0x40, 0x66, 0x40, 0x66, 0x40, 0x66, 0x60,
                              0x65, 0x70, 0, 0]), "HalfwayPageNybbles")
bowser_identities = find(bytes([6, 0, 2, 0x12, 0x11, 7, 5, 0x2D]), "BowserIdentities")
hidden_1up = find(bytes([0x15, 0x23, 0x16, 0x1B, 0x17, 0x18, 0x23, 0x63]), "Hidden1UpCoinAmts")

print("Table addresses (CPU):")
for n, o in [("WarpZoneNumbers", warp_zone_numbers), ("GameTextOffsets", game_text_offsets),
             ("WorldAddrOffsets", world_addr_offsets), ("AreaAddrOffsets", area_addr_offsets),
             ("EnemyAddrHOffsets", enemy_addr_hoffsets), ("EnemyDataAddrLow", enemy_data_addr_low),
             ("EnemyDataAddrHigh", enemy_data_addr_high), ("AreaDataHOffsets", area_data_hoffsets),
             ("AreaDataAddrLow", area_data_addr_low), ("AreaDataAddrHigh", area_data_addr_high),
             ("HalfwayPageNybbles", halfway_nybbles), ("BowserIdentities", bowser_identities),
             ("Hidden1UpCoinAmts", hidden_1up)]:
    print(f"  {n:20s} ${cpu(o):04X}")

# --- HandlePipeEntry: WZC -> WorldNumber -> AreaPointer --------------------------------------
def area_decode(ap):
    """GetAreaDataAddrs: AreaPointer -> (type, enemy data addr, level data addr)."""
    t = (ap >> 5) & 3
    lo = ap & 0x1F
    ei = rd(enemy_addr_hoffsets + t) + lo
    e_addr = rd(enemy_data_addr_low + ei) | (rd(enemy_data_addr_high + ei) << 8)
    li = rd(area_data_hoffsets + t) + lo
    l_addr = rd(area_data_addr_low + li) | (rd(area_data_addr_high + li) << 8)
    return t, ei, e_addr, li, l_addr

TYPE = ["water", "ground", "underground", "castle"]

def find_area_pointer(world, area):
    """FindAreaPointer / HandlePipeEntry: AreaAddrOffsets[WorldAddrOffsets[world] + area]."""
    x = (rd(world_addr_offsets + world) + area) & 0xFF
    return x, rd(area_addr_offsets + x)

print("\nHandlePipeEntry lookup for every WarpZoneControl value (index = (WZC&3)*4 + pipe):")
for wzc in range(8):
    for pipe, xr in enumerate(["X<$60", "$60<=X<$A0", "X>=$A0"]):
        idx = (wzc & 3) * 4 + pipe
        byte = rd(warp_zone_numbers + idx)
        world = (byte - 1) & 0xFF
        x, ap = find_area_pointer(world, 0)
        t, ei, ea, li, la = area_decode(ap)
        print(f"  WZC={wzc} pipe {pipe} ({xr:11s}): byte ${byte:02X} -> WorldNumber {world:3d} "
              f"(shows as world {byte:2d}); WorldAddrOffsets[{world}]=${rd(world_addr_offsets + world):02X} "
              f"-> AreaAddrOffsets[{x}]=${ap:02X} -> type {t} {TYPE[t]:11s} "
              f"enemy idx {ei:3d} @${ea:04X}, level idx {li:3d} @${la:04X}")

print("\nFindAreaPointer for the bogus worlds, AreaNumber 0..5 (what a flagpole/death would load):")
for world in (35, 38, 255):
    for area in range(6):
        x, ap = find_area_pointer(world, area)
        t, ei, ea, li, la = area_decode(ap)
        print(f"  world {world:3d} area {area}: AreaAddrOffsets[{x:3d}]=${ap:02X} type {TYPE[t]:11s} "
              f"enemy @${ea:04X} level @${la:04X}")

print("\nOther WorldNumber-indexed tables, OOB entries:")
for world in (35, 38, 255):
    hx = (world * 2) & 0xFF
    print(f"  world {world:3d}: HalfwayPageNybbles[{hx}]=${rd(halfway_nybbles + hx):02X} "
          f"[{hx + 1}]=${rd(halfway_nybbles + hx + 1):02X}; BowserIdentities[{world}]=${rd(bowser_identities + world):02X}; "
          f"Hidden1UpCoinAmts[{world}]=${rd(hidden_1up + world):02X}")

print("\nAreaAddrOffsets as listed (index: value type):")
for i in range(36):
    ap = rd(area_addr_offsets + i)
    print(f"  [{i:2d}] ${ap:02X} {TYPE[(ap >> 5) & 3]:11s} lo {ap & 0x1F:2d}", end="\n" if i % 3 == 2 else " | ")
