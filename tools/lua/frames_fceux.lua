-- Replay a movie in FCEUX (--playmov) and save one PNG per emulated frame for frames [FROM, TO]
-- (FCEUX frame numbers = QuickNES rows + 3, F25/P1.1). Env: OUTDIR, FROM, TO.
-- Run via tools/fceux_run.sh OUTDIR=... FROM=... TO=... --playmov movie.fm2 --loadlua this.lua ROM
emu.speedmode("nothrottle")
local OUTDIR = os.getenv("OUTDIR") or "/tmp/frames"
local FROM = tonumber(os.getenv("FROM") or "0")
local TO = tonumber(os.getenv("TO") or "0")
local i = 0
while true do
  emu.frameadvance()
  i = i + 1
  if i >= FROM and i <= TO then
    gui.savescreenshotas(string.format("%s/f%05d.png", OUTDIR, i))
  end
  if i > TO then break end
end
emu.exit()
