-- Mesen2 smoke test: run 300 frames, log FrameCounter/OperMode every 60 frames to a file, exit 0
local out = io.open(os.getenv("HOME") .. "/opt/mesen2/smoke_out.txt", "w")
local n = 0
local function onFrame()
  n = n + 1
  if n % 60 == 0 then
    local fc = emu.read(0x09, emu.memType.nesMemory)
    local om = emu.read(0x0770, emu.memType.nesMemory)
    out:write(string.format("frame=%d FrameCounter=%d OperMode=%d\n", n, fc, om))
  end
  if n >= 300 then
    out:write("done\n"); out:close()
    emu.stop(0)
  end
end
emu.addEventCallback(onFrame, emu.eventType.endFrame)
out:write("script loaded\n"); out:flush()
