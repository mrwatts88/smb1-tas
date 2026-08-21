local N = tonumber(os.getenv("BENCH_FRAMES") or "20000")
local n = 0
local function onFrame()
  n = n + 1
  if n >= N then
    local f = io.open("/home/mattwatts/Documents/smb1-tas/runs/bench_mesen2.txt", "w")
    f:write(string.format("frames=%d clock=%.3f\n", n, os.clock())); f:close()
    emu.stop(0)
  end
end
emu.addEventCallback(onFrame, emu.eventType.endFrame)
