local N = tonumber(os.getenv("BENCH_FRAMES") or "2000")
client.speedmode(6400); client.unpause()
local t0 = os.clock()
for i = 1, N do emu.frameadvance() end
local f = io.open("/home/mattwatts/Documents/smb1-tas/runs/bench_bizhawk.txt", "w")
f:write(string.format("frames=%d emu.framecount=%d cpu=%.3f FrameCounter=%d lagcount=%d\n", N, emu.framecount(), os.clock()-t0, memory.read_u8(0x09, "RAM"), emu.lagcount())); f:close()
client.exit()
