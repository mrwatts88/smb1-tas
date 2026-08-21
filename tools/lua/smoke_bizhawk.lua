-- BizHawk smoke test: run 300 frames, log FrameCounter/OperMode every 60 frames to a file, exit
local out = io.open(os.getenv("HOME") .. "/opt/bizhawk_smoke_out.txt", "w")
out:write("script loaded, emu.framecount=" .. tostring(emu.framecount()) .. " core=" .. tostring(emu.getsystemid()) .. "\n"); out:flush()
client.speedmode(800)
client.unpause()
for i = 1, 300 do
  emu.frameadvance()
  if i % 60 == 0 then
    out:write(string.format("frame=%d emu.framecount=%d FrameCounter=%d OperMode=%d lagcount=%d\n",
      i, emu.framecount(), memory.read_u8(0x09, "RAM"), memory.read_u8(0x0770, "RAM"), emu.lagcount()))
    out:flush()
  end
end
out:write("done\n"); out:close()
client.exit()
