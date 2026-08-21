emu.speedmode("nothrottle")
local N = tonumber(os.getenv("BENCH_FRAMES") or "2000")
local t0 = os.clock()
for i = 1, N do emu.frameadvance() end
local f = io.open(os.getenv("HOME") .. "/opt/fceux_bench_out.txt", "w")
f:write(string.format("frames=%d emu.framecount=%d cpu=%.3f FrameCounter=%d\n", N, emu.framecount(), os.clock()-t0, memory.readbyte(0x09))); f:close()
emu.exit()
