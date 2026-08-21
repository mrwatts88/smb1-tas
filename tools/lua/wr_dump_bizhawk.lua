-- BizHawk: replay a movie (use with --movie=) and dump key addresses per frame to <OUT>.csv
-- (same columns as wr_dump_fceux.lua, minus the full-RAM file) plus <OUT>.summary.
-- Env: OUT, MAXF (default 19000). Run via tools/bizhawk_run.sh OUT=... --movie=... --lua=this.lua ROM
local OUT  = os.getenv("OUT") or ("/home/mattwatts/Documents/smb1-tas/runs/wr_dump_bizhawk")
local MAXF = tonumber(os.getenv("MAXF") or "19000")
client.speedmode(6400); client.unpause()
local csv = io.open(OUT .. ".csv", "w")
csv:write("i,emu_frame,movie_frame,movie_mode,lag,lagcount,pad,OperMode,OperMode_Task,GameEngineSub,World,Level,AreaNum,IntervalTimerCtl,FrameCounter,TimerCtl,Player_PageLoc,Player_X,Player_Y,Player_State,PlayerStatus,ScreenLeft_Page,Timer_H,Timer_T,Timer_O,RNG0,RNG1,Player_X_Speed,EnemyFrameTimer\n")
local function rb(a) return memory.read_u8(a, "RAM") end
local function padbyte()
  local j = joypad.get(1)
  local v = 0
  if j.Right then v = v + 0x80 end
  if j.Left  then v = v + 0x40 end
  if j.Down  then v = v + 0x20 end
  if j.Up    then v = v + 0x10 end
  if j.Start then v = v + 0x08 end
  if j.Select then v = v + 0x04 end
  if j.B then v = v + 0x02 end
  if j.A then v = v + 0x01 end
  return v
end
local i, first_victory, first_game, movie_end = 0, nil, nil, nil
local mode0 = tostring(movie.mode())
while true do
  emu.frameadvance()
  i = i + 1
  local om = rb(0x0770)
  local mm = tostring(movie.mode())
  csv:write(string.format("%d,%d,%d,%s,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d\n",
    i, emu.framecount(), emu.framecount(), mm, emu.islagged() and 1 or 0, emu.lagcount(), padbyte(),
    om, rb(0x0772), rb(0x0e), rb(0x075f), rb(0x075c), rb(0x0760), rb(0x077f), rb(0x09), rb(0x0747),
    rb(0x6d), rb(0x86), rb(0xce), rb(0x1d), rb(0x0756), rb(0x071a),
    rb(0x07f8), rb(0x07f9), rb(0x07fa), rb(0x07a7), rb(0x07a8), rb(0x57), rb(0x078a)))
  if om == 1 and not first_game then first_game = i end
  if om == 2 and not first_victory then first_victory = i end
  if mm ~= "PLAY" and not movie_end then movie_end = i end
  if (first_victory and i >= first_victory + 400) or i >= MAXF then break end
end
csv:close()
local s = io.open(OUT .. ".summary", "w")
s:write(string.format("frames_dumped=%d\nmovie_mode_at_start=%s\nmovie_length=%s\nfirst_OperMode1_i=%s\nfirst_OperMode2_i=%s\nmovie_mode_left_PLAY_i=%s\nlagcount=%d\nemu_framecount=%d\n",
  i, mode0, tostring(movie.length()), tostring(first_game), tostring(first_victory), tostring(movie_end), emu.lagcount(), emu.framecount()))
s:close()
client.exit()
