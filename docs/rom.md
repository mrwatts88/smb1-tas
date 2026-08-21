# ROM — exactly what we need, and how to get it legitimately

## Which ROM
TASVideos #1715M was made on `Super Mario Bros. (W) [!].nes` (GoodNES name; No-Intro calls it
`Super Mario Bros. (World).nes`; older sets say `(JU) (PRG0)`). It is the standalone NTSC
cartridge image: NROM (mapper 0), 32 KiB PRG + 8 KiB CHR = 40,960 bytes of data (40,976 with
the 16-byte iNES header). A clean dump of a standalone US NES or Japanese Famicom *Super Mario
Bros.* cartridge should yield identical bytes — the hash check in P0.2 is the arbiter.

Not equivalent: the *SMB / Duck Hunt* and *SMB / Duck Hunt / World Class Track Meet*
multicarts (different image and mapper), the PAL cartridge (different timing; a separate
TASVideos branch), the FDS disk, *All-Stars*, and the NES Classic / Virtual Console / Switch
Online containers (same game data wrapped in DRM).

Expected MD5 (recollection — confirm in P0.2 from the `.fm2` `romChecksum` header line):
`811b027eaf99c2def7b933c5208636de`. `tools/verify_rom.py` (written in P0.2) prints the iNES
header fields plus headered and headerless MD5/SHA1 and compares them with the movie header.

## Legitimate ways to obtain it
1. **Dump a cartridge you own** (cleanest path). Used standalone SMB carts are cheap (~$10–25).
   Dumpers: INLretro (~$60–70), sanni's open-source Cart Reader (kit/DIY), or a CopyNES-type
   device. Output is an iNES file; verify the hash.
2. **Official copies you already own** (NES Classic Edition, Wii/Wii U/3DS Virtual Console,
   Switch Online) contain the same game data, but extracting it means circumventing the
   device's protection — legally distinct from dumping a cartridge, and not our plan.
3. **Not legitimate:** ROM sites, archive collections, torrents. The file is Nintendo's
   copyrighted work; TASVideos does not distribute ROMs and identifies them by hash only.

## Where it goes
`roms/` — gitignored, never committed, never pushed. Each machine that runs sessions needs
its own copy.
