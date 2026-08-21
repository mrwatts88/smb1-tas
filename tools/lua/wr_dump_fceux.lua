-- Replay a movie in FCEUX (use with --playmov) and dump, per emulated frame:
--   <OUT>.ram  : 2048 bytes of RAM ($0000-$07FF) per frame, frame-major (binary)
--   <OUT>.csv  : key addresses per frame (see header) + the joypad byte FCEUX reports
--   <OUT>.summary : first frame where OperMode==2 (axe touched; HandleAxeMetatile sets it), etc.
-- Stops 400 frames after OperMode first becomes 2, or at MAXF frames.
-- Env: OUT (base path), MAXF (default 19000). Run via tools/fceux_run.sh OUT=... --playmov ... --loadlua this.lua ROM
emu.speedmode("nothrottle")
local OUT  = os.getenv("OUT") or (os.getenv("HOME") .. "/opt/wr_dump")
local MAXF = tonumber(os.getenv("MAXF") or "19000")
local ram = io.open(OUT .. ".ram", "wb")
local csv = io.open(OUT .. ".csv", "w")
csv:write("i,emu_frame,movie_frame,movie_mode,lag,lagcount,pad,OperMode,OperMode_Task,GameEngineSub,World,Level,AreaNum,IntervalTimerCtl,FrameCounter,TimerCtl,Player_PageLoc,Player_X,Player_Y,Player_State,PlayerStatus,ScreenLeft_Page,Timer_H,Timer_T,Timer_O,RNG0,RNG1,Player_X_Speed,EnemyFrameTimer\n")
local function padbyte()
  local j = joypad.read(1)
  local v = 0
  if j.right then v = v + 0x80 end
  if j.left  then v = v + 0x40 end
  if j.down  then v = v + 0x20 end
  if j.up    then v = v + 0x10 end
  if j.start then v = v + 0x08 end
  if j.select then v = v + 0x04 end
  if j.B then v = v + 0x02 end
  if j.A then v = v + 0x01 end
  return v
end
local rb = memory.readbyte
local i, first_victory, first_game, movie_end = 0, nil, nil, nil
while true do
  emu.frameadvance()
  i = i + 1
  ram:write(memory.readbyterange(0, 0x800))
  local om = rb(0x0770)
  local mm = movie.mode() or "none"
  csv:write(string.format("%d,%d,%d,%s,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d\n",
    i, emu.framecount(), movie.framecount(), mm, emu.lagged() and 1 or 0, emu.lagcount(), padbyte(),
    om, rb(0x0772), rb(0x0e), rb(0x075f), rb(0x075c), rb(0x0760), rb(0x077f), rb(0x09), rb(0x0747),
    rb(0x6d), rb(0x86), rb(0xce), rb(0x1d), rb(0x0756), rb(0x071a),
    rb(0x07f8), rb(0x07f9), rb(0x07fa), rb(0x07a7), rb(0x07a8), rb(0x57), rb(0x078a)))
  if om == 1 and not first_game then first_game = i end
  if om == 2 and not first_victory then first_victory = i end
  if mm ~= "playback" and not movie_end then movie_end = i end
  if (first_victory and i >= first_victory + 400) or i >= MAXF then break end
end
ram:close(); csv:close()
local s = io.open(OUT .. ".summary", "w")
s:write(string.format("frames_dumped=%d\nfirst_OperMode1_i=%s\nfirst_OperMode2_i=%s\nmovie_mode_left_playback_i=%s\nlagcount=%d\nemu_framecount=%d\nmovie_framecount=%d\n",
  i, tostring(first_game), tostring(first_victory), tostring(movie_end), emu.lagcount(), emu.framecount(), movie.framecount()))
s:close()
emu.exit()
