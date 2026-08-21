-- FCEUX smoke test: run 300 frames, log FrameCounter/OperMode every 60 frames to a file, exit
local out = io.open(os.getenv("HOME") .. "/opt/fceux_smoke_out.txt", "w")
out:write("script loaded, emu.framecount=" .. tostring(emu.framecount()) .. "\n"); out:flush()
for i = 1, 300 do
  emu.frameadvance()
  if i % 60 == 0 then
    out:write(string.format("frame=%d emu.framecount=%d FrameCounter=%d OperMode=%d lagcount=%d\n",
      i, emu.framecount(), memory.readbyte(0x09), memory.readbyte(0x0770), emu.lagcount()))
  end
end
out:write("done\n"); out:close()
emu.exit()
